import datetime
import enum
import uuid
from typing import Dict, List, Optional, Union

from fastapi_users import models as fastapi_users_models
from pydantic import BaseModel


class DBBaseModel(BaseModel):
    id: uuid.UUID
    created: datetime.datetime

    class Config:
        orm_mode = True


class ShareType(str, enum.Enum):
    """
    READ holders can read
    WRITE holders can read and write
    OWN holders can read, write, delete, and share
    """

    READ = "read"
    READWRITE = "readwrite"
    OWN = "own"


class RootType(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNMANAGED = "unmanaged"


class UserBase(fastapi_users_models.BaseUser):
    username: str

    class Config:
        orm_mode = True


class UserCreate(UserBase, fastapi_users_models.BaseUserCreate):
    pass


class UserUpdate(UserBase, fastapi_users_models.BaseUserUpdate):
    pass


class UserDB(UserBase, fastapi_users_models.BaseUserDB):
    pass


class StorageNodeBase(BaseModel):
    name: str
    api_url: str


class StorageNodeCreate(StorageNodeBase):
    pass


class StorageNodeDB(DBBaseModel, StorageNodeBase):
    creator_id: uuid.UUID
    creator: UserBase


class WorkspaceRootBase(BaseModel):
    root_type: RootType
    bucket: str
    base_path: str


class WorkspaceRootCreate(WorkspaceRootBase):
    node_name: str


class WorkspaceRootDB(DBBaseModel, WorkspaceRootBase):
    node_id: uuid.UUID


class WorkspaceBase(BaseModel):
    name: str


class WorkspaceCreate(WorkspaceBase):
    public: Optional[bool] = False
    unmanaged: Optional[bool] = False
    node_name: Optional[str]


class WorkspaceDB(DBBaseModel, WorkspaceBase):
    id: uuid.UUID
    bucket: str
    name: str
    owner_id: uuid.UUID
    root_id: uuid.UUID
    owner: UserBase


class S3TokenBase(BaseModel):
    expiration: Optional[datetime.datetime]


class S3TokenCreate(S3TokenBase):
    workspaces: List[uuid.UUID]


class S3TokenSearch(BaseModel):
    search_terms: List[str]


class S3TokenDB(DBBaseModel, S3TokenBase):
    owner_id: uuid.UUID
    access_key_id: str
    secret_access_key: str
    session_token: str
    policy: dict
    bucket: str
    includes_owner_permissions: bool
    owner: UserBase
    workspaces: List[Union[WorkspaceDB, None]]


class S3TokenSearchResponseWorkspacePart(BaseModel):
    path: str
    workspace: WorkspaceDB


class S3TokenSearchResponse(BaseModel):
    token: Optional[S3TokenDB]
    workspaces: Dict[str, S3TokenSearchResponseWorkspacePart]


class ShareBase(BaseModel):
    workspace_id: uuid.UUID
    permission: ShareType
    expiration: Optional[datetime.datetime]


class ShareCreate(ShareBase):
    sharee_id: uuid.UUID


class ShareUpdate(ShareBase):
    pass


class ShareDB(DBBaseModel, ShareBase):
    creator_id: uuid.UUID
    sharee_id: uuid.UUID
    workspace: WorkspaceDB
    creator: UserBase
    sharee: UserBase


class IndexBase(BaseModel):
    s3_api_url: str
    s3_bucket: str
    s3_root: str
    index_type: str


class IndexCreate(IndexBase):
    pass


class IndexDB(DBBaseModel, IndexBase):
    s3_root: str


class IndexCreateResponse(BaseModel):
    commands: List[str]
    index: IndexDB

