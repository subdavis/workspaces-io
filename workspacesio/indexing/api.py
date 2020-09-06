import boto3
from botocore.client import Config
from elasticsearch import Elasticsearch
from fastapi import Depends
from fastapi.routing import APIRouter
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import SQLAlchemyUserDatabase

from workspacesio import database, schemas
from workspacesio.depends import fastapi_users, get_boto, get_db, get_elastic_client

from . import crud
from . import models as indexing_models
from . import schemas as indexing_schemas

router = APIRouter()


@router.post(
    "/index/{root_id}",
    tags=["index"],
    status_code=201,
    response_model=indexing_schemas.IndexDB,
)
def create_index(
    root_id: str,
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
    es: Elasticsearch = Depends(get_elastic_client),
):
    return crud.index_create(db, es, user, root_id)


@router.delete(
    "/index/{root_id}", tags=["index"], response_model=indexing_schemas.IndexDB
)
def delete_index(
    root_id: str,
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
    es: Elasticsearch = Depends(get_elastic_client),
):
    return crud.index_delete(db, es, user, root_id)


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
    """Minio issues HEAD on startup, I can't find documentation on how I should respond"""
    pass


@router.post(
    "/index_bulk",
    tags=["index"],
    status_code=201,
    response_model=indexing_schemas.IndexBulkAddedResponse,
)
def bulk_add(
    body: indexing_schemas.IndexBulkAdd,
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
    es: Elasticsearch = Depends(get_elastic_client),
):
    return crud.bulk_index_add(db, es, user, body)
