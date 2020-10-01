import datetime
import uuid
from typing import List, Optional

from pydantic import BaseModel

from workspacesio.schemas import DBBaseModel, WorkspaceDB


class DerivativeBase(BaseModel):
    workspace_id: uuid.UUID
    object_path: str
    object_name: str
    name: str
    object_revision_date: datetime.datetime


class DerviativeCreate(DerivativeBase):
    pass


class DerivativeDB(DerivativeBase, DBBaseModel):
    workspace: WorkspaceDB
