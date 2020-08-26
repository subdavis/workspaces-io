import datetime
import enum
import uuid
from typing import List, Optional, Union

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


class WorkspaceBase(BaseModel):
    public: Optional[bool]
    name: str


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceDB(DBBaseModel, WorkspaceBase):
    id: uuid.UUID
    public: bool
    bucket: str
    name: str
    owner_id: uuid.UUID
    owner: UserBase


class S3TokenBase(BaseModel):
    expiration: Optional[datetime.datetime]


class S3TokenCreate(S3TokenBase):
    workspaces: List[Union[uuid.UUID, None]]


class S3TokenSearch(BaseModel):
    workspace_name: Union[str, None]
    owner_name: Union[str, None]


class S3TokenDB(DBBaseModel, S3TokenBase):
    owner_id: uuid.UUID
    access_key_id: str
    secret_access_key: str
    session_token: str
    policy: dict
    bucket: str
    owner: UserBase
    workspaces: List[Union[WorkspaceDB, None]]


class S3TokenSearchResponse(BaseModel):
    token: S3TokenDB
    workspaces: List[WorkspaceDB]

    class Config:
        orm_mode = True


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
