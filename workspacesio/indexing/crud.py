import hashlib
import json
import urllib
from typing import Optional

import boto3
import elasticsearch
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from workspacesio import models, s3utils, schemas
from workspacesio.depends import Boto3ClientCache

from . import models as indexing_models
from . import schemas as indexing_schemas


def make_record_primary_key(
    api_url: str, bucket: str, workspace_prefix: str, path: str,
):
    primary_key = "".join([api_url, bucket, workspace_prefix, path]).encode("utf-8")
    return hashlib.sha256(primary_key).hexdigest()[-16:]


def index_create(
    db: Session, es: elasticsearch.Elasticsearch, user: schemas.UserDB, root_id: str,
) -> indexing_schemas.IndexDB:
    """Setup notifications and indexing for a root
    * Verify that the index exists in elasticsearch
    * Insert or update an index record
    """

    index_db: Optional[indexing_models.ElasticIndex] = db.query(
        indexing_models.ElasticIndex
    ).filter(indexing_models.ElasticIndex.root_id == root_id).first()
    if index_db is None:
        root: models.WorkspaceRoot = db.query(models.WorkspaceRoot).get_or_404(root_id)
        if root.storage_node.creator_id != user.id:
            raise PermissionError("User must be node operator to create index")
        index_db = indexing_models.ElasticIndex(root_id=root.id, index_type="default",)
        index_name = index_db.index_type
        db.add(index_db)
        db.flush()
        es.indices.create(
            index_name, body={"mappings": indexing_schemas.INDEX_DOCUMENT_MAPPING}
        )
        db.commit()
        db.refresh(index_db)
    return index_db


def bulk_index_add(
    db: Session,
    ec: elasticsearch.Elasticsearch,
    user: schemas.UserDB,
    docs: indexing_schemas.IndexBulkAdd,
):
    workspace: models.Workspace = db.query(models.Workspace).get_or_404(
        docs.workspace_id
    )
    root: models.WorkspaceRoot = workspace.root
    bulk_operations = ""
    index: indexing_models.ElasticIndex = db.query(indexing_models.ElasticIndex).filter(
        indexing_models.ElasticIndex.root_id == root.id
    ).first()
    if index is None:
        raise ValueError(
            f"index does not exist for workspace {workspace.name}::{workspace.id}"
        )
    for doc in docs.documents:
        workspacekey = s3utils.getWorkspaceKey(workspace)
        upsertdoc = indexing_schemas.IndexDocument(
            time=doc.time,
            size=doc.size,
            eTag=doc.eTag or "",
            workspace_id=workspace.id,
            workspace_name=workspace.name,
            owner_id=workspace.owner_id,
            owner_name=workspace.owner.username,
            bucket=root.bucket,
            server=root.storage_node.api_url,
            root=workspacekey,
            path=doc.path,
            user_shares=[share.sharee.id for share in workspace.shares],
            # TODO: group shares
        )
        bulk_operations += (
            json.dumps(
                {
                    "update": {
                        "_index": index.index_type,
                        "_id": make_record_primary_key(
                            root.storage_node.api_url,
                            root.bucket,
                            workspacekey,
                            doc.path,
                        ),
                    }
                },
            )
            + "\n"
        )
        bulk_operations += (
            indexing_schemas.ElasticUpsertIndexDocument(doc=upsertdoc).json() + "\n"
        )
    ec.bulk(bulk_operations)


def handle_bucket_event(
    db: Session,
    ec: elasticsearch.Elasticsearch,
    event: indexing_schemas.BucketEventNotification,
):
    # Find workspace for event
    bulk_operations = ""
    for record in event.Records:
        bucket = record.s3.bucket.name
        # TODO: find the root, which will give us the naming convention
        # for child buckets
        # For now, find the index
        object_key = urllib.parse.unquote(record.s3.object.key)
        parent_index: indexing_models.ElasticIndex = db.query(
            indexing_models.ElasticIndex
        ).filter(
            func.strpos(indexing_models.ElasticIndex.s3_root, object_key) == 0
        ).first()
        if parent_index is None:
            raise ValueError(f"no index for object {object_key}")
        # TODO: skip the part where we extrapolate workspace name, assume it's {scope}/{user}/{workspace}
        key_parts = object_key.split("/")
        scope = key_parts[0]
        user_name = key_parts[1]
        workspace_name = key_parts[2]
        workspace_inner_path = "/".join(key_parts[3:])
        # TODO: server and root will have to be joined.
        resource_owner: models.User = db.query(models.User).filter(
            models.User.username == user_name
        ).first()
        if resource_owner is None:
            raise ValueError(f"no owner found for object {object_key}")
        workspace: models.Workspace = db.query(models.Workspace).filter(
            and_(
                models.Workspace.name == workspace_name,
                models.Workspace.owner == resource_owner,
            )
        ).first()
        if workspace is None:
            raise ValueError(f"no workspace found for object {object_key}")

        primary_key = (
            f"{parent_index.s3_api_url}:{parent_index.s3_bucket}"
            f":{parent_index.s3_root}:{object_key}"
        ).encode("utf-8")
        primary_key_short_sha256 = hashlib.sha256(primary_key).hexdigest()[-16:]
        if record.eventName in [
            "s3:ObjectCreated:Put",
            "s3:ObjectCreated:Post",
            "s3:ObjectCreated:Copy",
        ]:
            # Creaete a new record in elasticsearch
            # this could be an overwrite operation, so query for the old record first.
            doc = indexing_schemas.IndexDocument(
                time=record.eventTime,
                size=record.s3.object.size,
                eTag=record.s3.object.eTag,
                workspace_id=workspace.id,
                workspace_name=workspace.name,
                owner_id=resource_owner.id,
                owner_name=resource_owner.username,
                bucket=record.s3.bucket.name,
                server=parent_index.s3_api_url,
                root=parent_index.s3_root,
                path=workspace_inner_path,
                user_shares=[share.sharee.id for share in workspace.shares],
                # TODO: group shares
            )
            bulk_operations += (
                json.dumps(
                    {
                        "update": {
                            "_index": parent_index.index_type,
                            "_id": primary_key_short_sha256,
                        }
                    },
                )
                + "\n"
            )
            bulk_operations += (
                indexing_schemas.ElasticUpsertIndexDocument(doc=doc).json() + "\n"
            )

        elif record.eventName in ["s3:ObjectRemoved:Delete"]:
            # Remove an existing record
            bulk_operations += (
                json.dumps(
                    {
                        "delete": {
                            "_index": parent_index.index_type,
                            "_id": primary_key_short_sha256,
                        }
                    }
                )
                + "\n"
            )
        else:
            raise ValueError(
                f"Bucket notification type unsupported: {record.eventName}"
            )
    ec.bulk(bulk_operations)
