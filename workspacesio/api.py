import uuid
from typing import List, Optional

import boto3
from botocore import UNSIGNED
from botocore.client import Config
from fastapi import Depends
from fastapi.routing import APIRouter
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import SQLAlchemyUserDatabase

from . import crud, database, dbutils, models, schemas, settings

router = APIRouter()
user_db = SQLAlchemyUserDatabase(
    schemas.UserBase, database.database, models.User.__table__
)
jwt_authentication = JWTAuthentication(
    secret=settings.SECRET, lifetime_seconds=3600, tokenUrl="/auth/jwt/login"
)
fastapi_users = FastAPIUsers(
    user_db,
    [jwt_authentication],
    schemas.UserBase,
    schemas.UserCreate,
    schemas.UserUpdate,
    schemas.UserBase,
)


def get_db():
    db = database.SessionLocal(query_cls=dbutils.Query)
    try:
        yield db
    finally:
        db.close()


def get_boto_s3():
    yield boto3.client(
        "s3",
        region_name=settings.AWS_REGION_NAME,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )


def get_boto_sts():
    yield boto3.client(
        "sts",
        region_name=settings.AWS_REGION_NAME,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


@router.get("/me", response_model=schemas.UserBase, tags=["user"])
def get_me(user: schemas.UserBase = Depends(fastapi_users.get_current_user)):
    return user


@router.get("/workspace", response_model=List[schemas.WorkspaceDB], tags=["workspace"])
def list_workspaces(
    name: Optional[str] = None,
    owner_id: Optional[str] = None,
    public: Optional[bool] = False,
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.workspace_search(db, user, name=name, public=public, owner_id=owner_id)


@router.post(
    "/workspace",
    response_model=schemas.WorkspaceDB,
    tags=["workspace"],
    status_code=201,
)
def create_workspace(
    workspace: schemas.WorkspaceCreate,
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
    boto_s3: boto3.Session = Depends(get_boto_s3),
):
    return crud.workspace_create(db, boto_s3, workspace, user)


@router.get("/token", response_model=List[schemas.S3TokenDB], tags=["token"])
def list_tokens(
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.token_list(db, user)


@router.post(
    "/token", response_model=schemas.S3TokenDB, tags=["token"], status_code=201
)
def create_token(
    token: schemas.S3TokenCreate,
    db: database.SessionLocal = Depends(get_db),
    boto_sts: boto3.Session = Depends(get_boto_sts),
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
):
    return crud.token_create(db, boto_sts, user, token)


@router.post(
    "/token/search", response_model=schemas.S3TokenSearchResponse, tags=["token"]
)
def search_token(
    terms: schemas.S3TokenSearch,
    db: database.SessionLocal = Depends(get_db),
    boto_sts: boto3.Session = Depends(get_boto_sts),
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
):
    return crud.token_search(db, boto_sts, user, terms)


@router.delete("/token/{token_id}", tags=["token"])
def revoke_token(
    token_id: str,
    db: database.SessionLocal = Depends(get_db),
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
):
    return crud.token_revoke(db, uuid.UUID(token_id))


@router.delete("/token", tags=["token"], response_model=int)
def revoke_all_tokens(
    db: database.SessionLocal = Depends(get_db),
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
):
    return crud.token_revoke_all(db, user)


@router.post("/share", response_model=schemas.ShareDB, tags=["share"], status_code=201)
def create_workspace_share(
    share: schemas.ShareCreate,
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.share_create(db, user, share)
