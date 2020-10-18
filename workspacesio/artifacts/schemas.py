import datetime
import uuid
from typing import List, Optional

from pydantic import BaseModel

from workspacesio.schemas import DBBaseModel, WorkspaceDB


class ArtifactBase(BaseModel):
    workspace_id: uuid.UUID
    object_path: str
    object_name: str
    name: str
    object_revision_date: datetime.datetime


class DerviativeCreate(ArtifactBase):
    pass


class ArtifactDB(ArtifactBase, DBBaseModel):
    workspace: WorkspaceDB
