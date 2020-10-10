import uuid

import boto3
from botocore.client import Config
from elasticsearch import Elasticsearch
from fastapi import Depends
from fastapi.routing import APIRouter

from workspacesio import database, schemas
from workspacesio.auth import depends as auth_depends
from workspacesio.depends import get_boto, get_db, get_elastic_client

from . import crud
from . import models as indexing_models
from . import schemas as indexing_schemas

router = APIRouter()


@router.post(
    "/root/{root_id}/index",
    tags=["root"],
    status_code=201,
    response_model=indexing_schemas.IndexDB,
)
def create_index(
    root_id: uuid.UUID,
    user: schemas.UserBase = Depends(auth_depends.get_current_user),
    db: database.SessionLocal = Depends(get_db),
    es: Elasticsearch = Depends(get_elastic_client),
):
    return crud.root_index_upsert(db, es, user, root_id)


@router.delete(
    "/root/{root_id}/index", tags=["root"], response_model=indexing_schemas.IndexDB
)
def delete_index(
    root_id: uuid.UUID,
    user: schemas.UserBase = Depends(auth_depends.get_current_user),
    db: database.SessionLocal = Depends(get_db),
    es: Elasticsearch = Depends(get_elastic_client),
):
    return crud.root_index_delete(db, es, user, root_id)


@router.post(
    "/workspace/{workspace_id}/crawl",
    tags=["workspace"],
    status_code=201,
    response_model=indexing_schemas.WorkspaceCrawlRoundDB,
)
def create_workspace_crawl(
    workspace_id: uuid.UUID,
    user: schemas.UserBase = Depends(auth_depends.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    """
    Create a new crawl round or return the current open crawl
    """
    return crud.workspace_crawl_create(db, user, workspace_id)


@router.post(
    "/minio/events",
    tags=["hooks"],
    status_code=200,
)
def create_event(
    body: indexing_schemas.BucketEventNotification,
    db: database.SessionLocal = Depends(get_db),
    es: Elasticsearch = Depends(get_elastic_client),
):
    return crud.handle_bucket_event(db, es, body)


@router.head("/minio/events", tags=["hooks"], status_code=200)
def head_event():
    """MinIO issues HEAD on startup"""
    pass


@router.post(
    "/workspace/{workspace_id}/bulk_index",
    tags=["index"],
    status_code=201,
    response_model=indexing_schemas.IndexBulkAddedResponse,
)
def bulk_add(
    workspace_id: uuid.UUID,
    body: indexing_schemas.IndexBulkAdd,
    user: schemas.UserBase = Depends(auth_depends.get_current_user),
    db: database.SessionLocal = Depends(get_db),
    es: Elasticsearch = Depends(get_elastic_client),
):
    return crud.bulk_index_add(db, es, user, workspace_id, body)
