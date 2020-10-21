import datetime
import enum
import uuid
from typing import Dict, List, Optional, Tuple, Union

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


class ServerInfo(BaseModel):
    public_address: str


###########################################################
# User Schemas
###########################################################


class UserBase(BaseModel):
    username: str


class UserDB(DBBaseModel, UserBase):
    pass


###########################################################
# Storage Node Schemas
###########################################################


class StorageNodeBase(BaseModel):
    name: str
    api_url: str
    sts_api_url: Optional[str]
    region_name: str


class StorageNodeCreate(StorageNodeBase):
    access_key_id: str
    secret_access_key: str
    assume_role_arn: Optional[str]


class StorageNodeDB(DBBaseModel, StorageNodeBase):
    creator_id: uuid.UUID
    creator: UserDB


class StorageNodeOperator(StorageNodeDB):
    access_key_id: str
    secret_access_key: str
    assume_role_arn: Optional[str]


###########################################################
# Workspace Root Schemas
###########################################################


class WorkspaceRootBase(BaseModel):
    root_type: RootType
    bucket: str
    base_path: str


class WorkspaceRootCreate(WorkspaceRootBase):
    node_name: str


class WorkspaceRootDB(DBBaseModel, WorkspaceRootBase):
    node_id: uuid.UUID


class WorkspaceRootOperator(WorkspaceRootDB):
    storage_node: StorageNodeDB


###########################################################
# RootCredentials Schemas
###########################################################


class RootCredentials(BaseModel):
    """
    Only passed out to node operators
    and administrators
    """

    root: WorkspaceRootOperator
    node: StorageNodeOperator


###########################################################
# Workspace Schemas
###########################################################


class WorkspaceBase(BaseModel):
    name: str
    base_path: Optional[str]


class WorkspaceCreate(WorkspaceBase):
    public: Optional[bool] = False
    unmanaged: Optional[bool] = False
    node_name: Optional[str]
    root_id: Optional[uuid.UUID]


class WorkspaceDB(DBBaseModel, WorkspaceBase):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    root_id: uuid.UUID
    owner: UserDB
    root: WorkspaceRootDB


###########################################################
# API Key Schemas
###########################################################


class ApiKeyBase(BaseModel):
    pass


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKeyCreateResponse(DBBaseModel, ApiKeyBase):
    key_id: str
    secret: str
    user_id: uuid.UUID


class ApiKeyDB(DBBaseModel, ApiKeyBase):
    key_id: str
    user_id: uuid.UUID

    user: UserDB


###########################################################
# S3 Token Schemas
###########################################################


class S3TokenBase(BaseModel):
    expiration: Optional[datetime.datetime]


class S3TokenCreate(S3TokenBase):
    workspaces: List[uuid.UUID]


class S3TokenSearch(BaseModel):
    search_terms: List[str]


class S3TokenDB(DBBaseModel, S3TokenBase):
    owner_id: uuid.UUID
    storage_node_id: uuid.UUID
    access_key_id: str
    secret_access_key: str
    session_token: str
    policy: dict
    owner: UserDB
    workspaces: List[WorkspaceDB]


class S3TokenSearchResponseWorkspacePart(BaseModel):
    path: str
    workspace: WorkspaceDB


class TokenNodeWrapper(BaseModel):
    token: S3TokenDB
    node: StorageNodeDB


class S3TokenSearchResponse(BaseModel):
    tokens: List[TokenNodeWrapper]
    workspaces: Dict[str, S3TokenSearchResponseWorkspacePart]


###########################################################
# Share Schemas
###########################################################


class ShareBase(BaseModel):
    permission: ShareType
    expiration: Optional[datetime.datetime]


class ShareCreate(ShareBase):
    sharee_id: Optional[uuid.UUID]
    workspace_id: Optional[uuid.UUID]
    sharee: Optional[str]
    workspace: Optional[str]


class ShareUpdate(ShareBase):
    pass


class ShareDB(DBBaseModel, ShareBase):
    creator_id: uuid.UUID
    workspace_id: uuid.UUID
    sharee_id: uuid.UUID
    workspace: WorkspaceDB
    creator: UserDB
    sharee: UserDB


###########################################################
# Instrumentation Schemas
###########################################################


class InstrumentBase(BaseModel):
    tag: str
    enabled: bool


class InstrumentUpdate(InstrumentBase):
    pass


class InstrumentDB(InstrumentBase, DBBaseModel):
    last_updated: datetime.datetime
    pulled_size: int
    pushed_size: int
    pulled_count: int
    pushed_count: int
