import uuid
from typing import List, Optional, Tuple, Union

import boto3

from elasticsearch import Elasticsearch
from fastapi import Depends
from fastapi.routing import APIRouter


from . import crud, database, schemas
from .depends import get_boto, get_db, fastapi_users


router = APIRouter()


@router.get("/node", response_model=List[schemas.StorageNodeDB], tags=["node"])
def list_nodes(
    _: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.node_search(db)


@router.post("/node", response_model=schemas.StorageNodeDB, tags=["node"])
def create_node(
    params: schemas.StorageNodeCreate,
    creator: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.node_create(db, creator, params)


@router.get("/node/root", response_model=List[schemas.WorkspaceRootDB], tags=["node"])
def list_node_roots(
    node_name: Optional[str] = None,
    _: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.root_search(db, node_name=node_name)


@router.post("/node/root", response_model=schemas.WorkspaceRootDB, tags=["node"])
def create_node_root(
    params: schemas.WorkspaceRootCreate,
    creator: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
    boto_s3: boto3.Session = Depends(get_boto),
):
    return crud.root_create(db, boto_s3, creator, params)


@router.get("/workspace", response_model=List[schemas.WorkspaceDB], tags=["workspace"])
def list_workspaces(
    name: Optional[str] = None,
    owner_id: Optional[str] = None,
    public: Optional[bool] = False,
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.workspace_search(db, user, name=name, public=public, owner_id=owner_id)


@router.get(
    "/workspace/{workspace_id}", response_model=schemas.WorkspaceDB, tags=["workspace"],
)
def get_workspace(
    workspace_id: str,
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.workspace_get(db, user, workspace_id)


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
    boto_s3: boto3.Session = Depends(get_boto),
):
    return crud.workspace_create(db, boto_s3, workspace, user)


@router.post(
    "/workspace/share",
    response_model=schemas.ShareDB,
    tags=["workspace"],
    status_code=201,
)
def create_workspace_share(
    share: schemas.ShareCreate,
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.share_create(db, user, share)


@router.get("/token", response_model=List[schemas.S3TokenDB], tags=["token"])
def list_tokens(
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.token_list(db, user)


@router.post(
    "/token", response_model=List[schemas.S3TokenDB], tags=["token"], status_code=201
)
def create_token(
    token: schemas.S3TokenCreate,
    db: database.SessionLocal = Depends(get_db),
    boto_sts: boto3.Session = Depends(get_boto),
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
):
    return crud.token_create(db, boto_sts, user, token)


@router.post(
    "/token/search", response_model=schemas.S3TokenSearchResponse, tags=["token"]
)
def search_token(
    terms: schemas.S3TokenSearch,
    db: database.SessionLocal = Depends(get_db),
    boto_sts: boto3.Session = Depends(get_boto),
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

