import hashlib
import json
import urllib

import boto3
import elasticsearch
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from workspacesio import models, schemas
from workspacesio.depends import Boto3ClientCache

from . import models as indexing_models
from . import schemas as indexing_schemas


def index_create(
    db: Session, b3: Boto3ClientCache, es: elasticsearch.Elasticsearch
) -> indexing_schemas.IndexDB:
    """Setup notifications and indexing for a root
    * Provide a command for the operator to create the notification stream
    * Verify that the index exists in elasticsearch
    * Insert or update an index record
    """

    public_index: Optional[indexing_models.ElasticIndex] = db.query(
        indexing_models.ElasticIndex
    ).filter(indexing_models.ElasticIndex.public == True).first()
    if public_index is None:
        public_index = indexing_models.ElasticIndex(
            public=True,
            s3_api_url="http://minio:9000",
            s3_bucket="fast",
            s3_root="public".lstrip("/"),
            index_type="default",
        )
        index_name = public_index.index_type
        db.add(public_index)
        db.flush()
        es.indices.create(
            index_name, body={"mappings": indexing_schemas.INDEX_DOCUMENT_MAPPING}
        )
        db.commit()
        db.refresh()
    return public_index


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
                indexing_schemas.UpsertIndexDocument(doc=doc).json() + "\n"
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
