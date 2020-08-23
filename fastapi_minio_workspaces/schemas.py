import datetime
import enum
import uuid
from typing import List, Optional

from fastapi_users import models as fastapi_users_models
from pydantic import BaseModel


class DBBaseModel(BaseModel):
    id: uuid.UUID
    created: datetime.datetime


class ShareType(enum.Enum):
    """
    READ holders can read
    WRITE holders can read and write
    OWN holders can read, write, delete, and share
    """

    READ = 1
    READWRITE = 2
    OWN = 3


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


class WorkspaceListItem(DBBaseModel, WorkspaceBase):
    permission: Optional[ShareType]


class WorkspaceCreate(WorkspaceBase):
    pass


class WorspaceDB(DBBaseModel, WorkspaceBase):
    id: uuid.UUID
    public: bool
    bucket: str
    name: str
    owner_id: int

    class Config:
        orm_mode = True


class S3TokenBase(BaseModel):
    expiration: Optional[datetime.datetime]
    workspace_id: Optional[uuid.UUID]
    owner_id: uuid.UUID


class S3TokenCreate(S3TokenBase):
    pass


class S3TokenDB(DBBaseModel, S3TokenBase):
    access_key_id: str
    secret_access_key: str
    session_token: str
    owner: UserBase

    class Config:
        orm_mode = True


class ShareBase(BaseModel):
    workspace_id: uuid.UUID
    sharee_id: uuid.UUID
    permission: ShareType
    expiration: datetime.datetime


class ShareCreate(ShareBase):
    pass


class ShareDB(DBBaseModel, ShareBase):
    creator_id: uuid.UUID
    workspace: WorkspaceListItem
    creator: UserBase
    sharee: UserBase
