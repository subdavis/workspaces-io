import uuid
from typing import List, Optional, Tuple, Union

import boto3
from elasticsearch import Elasticsearch
from fastapi import Depends
from fastapi.routing import APIRouter

from workspacesio import auth, crud, database, models
from workspacesio.common import schemas
from workspacesio.depends import get_boto, get_db
from workspacesio.settings import settings

router = APIRouter()


@router.get("/info", response_model=schemas.ServerInfo, tags=["info"])
def get_info():
    return schemas.ServerInfo(public_address=settings.public_name)


@router.get("/users/me", response_model=schemas.UserDB, tags=["user"])
def get_users_me(me: models.User = Depends(auth.get_current_user)):
    return me


@router.get("/node", response_model=List[schemas.StorageNodeDB], tags=["node"])
def list_nodes(
    _: models.User = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.node_search(db)


@router.delete("/node/{node_id}", tags=["node"])
def remove_node(
    node_id: str,
    db: database.SessionLocal = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    return crud.node_delete(db, user, node_id)


@router.post("/node", response_model=schemas.StorageNodeDB, tags=["node"])
def create_node(
    params: schemas.StorageNodeCreate,
    creator: models.User = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.node_create(db, creator, params)


@router.get("/root", response_model=List[schemas.WorkspaceRootDB], tags=["root"])
def list_node_roots(
    node_name: Optional[str] = None,
    _: models.User = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.root_search(db, node_name=node_name)


@router.post("/root", response_model=schemas.WorkspaceRootDB, tags=["root"])
def create_node_root(
    params: schemas.WorkspaceRootCreate,
    creator: models.User = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
    boto_s3: boto3.Session = Depends(get_boto),
):
    return crud.root_create(db, boto_s3, creator, params)


@router.delete("/root/{root_id}", tags=["root"])
def delete_node_root(
    root_id: uuid.UUID,
    creator: models.User = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.root_delete(db, creator, root_id)


@router.post("/root/import", response_model=schemas.RootImport, tags=["root"])
def start_root_import(
    params: schemas.RootImportCreate,
    creator: models.User = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.root_start_import(db, creator, root_id=params.root_id)


@router.get("/workspace", response_model=List[schemas.WorkspaceDB], tags=["workspace"])
def list_workspaces(
    name: Optional[str] = None,
    owner_id: Optional[str] = None,
    like: Optional[str] = None,
    public: Optional[bool] = False,
    user: models.User = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.workspace_search(
        db, user, name=name, public=public, owner_id=owner_id, like=like
    )


@router.get(
    "/workspace/{workspace_id}",
    response_model=schemas.WorkspaceDB,
    tags=["workspace"],
)
def get_workspace(
    workspace_id: uuid.UUID,
    user: models.User = Depends(auth.get_current_user),
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
    user: models.User = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
    boto_s3: boto3.Session = Depends(get_boto),
):
    return crud.workspace_create(db, boto_s3, workspace, user)


@router.delete("/workspace/{workspace_id}", tags=["workspace"])
def delete_workspace(
    workspace_id: uuid.UUID,
    user: models.User = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.workspace_delete(db, user, workspace_id)


@router.post(
    "/workspace/share",
    response_model=schemas.ShareDB,
    tags=["workspace"],
    status_code=201,
)
def create_workspace_share(
    share: schemas.ShareCreate,
    user: models.User = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.share_create(db, user, share)


@router.get("/apikey", response_model=List[schemas.ApiKeyDB], tags=["apikey"])
def list_api_keys(
    user: models.User = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.apikey_list(db, user)


@router.post(
    "/apikey",
    response_model=schemas.ApiKeyCreateResponse,
    tags=["apikey"],
    status_code=201,
)
def create_apikey(
    user: models.User = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.apikey_create(db, user)


@router.get("/token", response_model=List[schemas.S3TokenDB], tags=["token"])
def list_tokens(
    user: models.User = Depends(auth.get_current_user),
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
    user: models.User = Depends(auth.get_current_user),
):
    return crud.token_create(db, boto_sts, user, token)


@router.post(
    "/token/search", response_model=schemas.S3TokenSearchResponse, tags=["token"]
)
def search_token(
    terms: schemas.S3TokenSearch,
    db: database.SessionLocal = Depends(get_db),
    boto_sts: boto3.Session = Depends(get_boto),
    user: models.User = Depends(auth.get_current_user),
):
    return crud.token_search(db, boto_sts, user, terms)


@router.delete("/token/{token_id}", tags=["token"])
def revoke_token(
    token_id: uuid.UUID,
    db: database.SessionLocal = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    return crud.token_revoke(db, token_id)


@router.delete("/token", tags=["token"], response_model=int)
def revoke_all_tokens(
    db: database.SessionLocal = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    return crud.token_revoke_all(db, user)
