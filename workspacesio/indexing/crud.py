import hashlib
import json
import posixpath
import urllib
from typing import Optional

import boto3
import elasticsearch
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from workspacesio import crud, models, s3utils, schemas
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
            index=index_name, body={"mappings": indexing_schemas.INDEX_DOCUMENT_MAPPING}
        )
        db.commit()
        db.refresh(index_db)
    return index_db


def index_delete(
    db: Session, es: elasticsearch.Elasticsearch, user: schemas.UserDB, root_id: str,
):
    index_db: indexing_models.ElasticIndex = db.query(
        indexing_models.ElasticIndex
    ).filter(indexing_models.ElasticIndex.root_id == root_id).first()
    if index_db is None:
        raise ValueError("No index with that id")
    es.indices.delete(index=index_db.index_type, ignore=[404])
    db.delete(index_db)
    db.commit()
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
            **doc.dict(),
            workspace_id=workspace.id,
            workspace_name=workspace.name,
            owner_id=workspace.owner_id,
            owner_name=workspace.owner.username,
            bucket=root.bucket,
            server=root.storage_node.api_url,
            root_path=workspacekey,
            root_id=root.id,
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

        object_key = urllib.parse.unquote(record.s3.object.key)
        parent_index: indexing_models.ElasticIndex = (
            db.query(indexing_models.ElasticIndex)
            .join(models.WorkspaceRoot)
            .filter(
                and_(
                    func.strpos(models.WorkspaceRoot.base_path, object_key) == 0,
                    models.WorkspaceRoot.bucket == record.s3.bucket.name,
                )
            )
            .first()
        )
        if parent_index is None:
            raise ValueError(f"no index for object {object_key}")

        # Find the workspace
        workspace: Optional[models.Workspace] = None
        workspace_prefix = ""
        workspace_inner_path = ""
        if parent_index.root.root_type in [
            schemas.RootType.PRIVATE,
            schemas.RootType.PRIVATE,
        ]:
            # Extrapolate path parts from root type, assume it's {scope}/{user}/{workspace}
            key_parts = object_key.split("/")
            scope = key_parts[0]
            user_name = key_parts[1]
            workspace_name = key_parts[2]
            workspace_inner_path = "/".join(key_parts[3:])
            workspace = (
                db.query(models.Workspace)
                .join(models.User)
                .filter(
                    and_(
                        models.Workspace.name == workspace_name,
                        models.User.username == user_name,
                    )
                )
                .first()
            )
            workspace_prefix = f"{scope}/{user_name}/{workspace_name}"

        elif parent_index.root.root_type == schemas.RootType.UNMANAGED:
            # Search again for matching base
            workspace_inner_path = object_key.lstrip(
                parent_index.root.base_path
            ).lstrip("/")
            workspace = (
                db.query(models.Workspace)
                .filter(
                    func.strpos(models.Workspace.base_path, workspace_inner_path) == 0
                )
                .first()
            )
            if workspace is None:
                raise ValueError(f"No workspace found for object {object_key}")

            workspace_prefix = workspace.base_path
            workspace_inner_path = workspace_inner_path.lstrip(
                workspace.base_path
            ).lstrip("/")

        if workspace is None:
            raise ValueError(f"No workspace found for object {object_key}")
        resource_owner: models.User = workspace.owner
        root: models.WorkspaceRoot = workspace.root
        node: models.StorageNode = root.storage_node

        primary_key_short_sha256 = make_record_primary_key(
            api_url=node.api_url,
            bucket=root.bucket,
            workspace_prefix=workspace_prefix,
            path=workspace_inner_path,
        )
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
                server=node.api_url,
                root_path=root.base_path,
                root_id=root.id,
                path=workspace_inner_path,
                extension=posixpath.splitext(workspace_inner_path)[-1],
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
