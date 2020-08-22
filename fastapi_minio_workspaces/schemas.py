import enum
from typing import Optional
import uuid

from fastapi_users import models as fastapi_users_models
from pydantic import BaseModel


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


class UserCreate(UserBase, fastapi_users_models.BaseUserCreate):
    pass


class UserUpdate(UserBase, fastapi_users_models.BaseUserUpdate):
    pass


class UserDB(UserBase, fastapi_users_models.BaseUserDB):
    pass


class WorkspaceBase(BaseModel):
    public: Optional[bool]
    name: str


class WorkspaceListItem(WorkspaceBase):
    permission: Optional[ShareType]


class WorkspaceCreate(WorkspaceBase):
    pass


class WorspaceDB(WorkspaceBase):
    id: uuid.UUID
    public: bool
    bucket: str
    name: str
    owner_id: int

    class Config:
        orm_mode = True
