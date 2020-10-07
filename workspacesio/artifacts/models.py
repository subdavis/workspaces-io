from sqlalchemy import Column, ForeignKey, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from workspacesio.models import BaseModel, Workspace


class Artifact(BaseModel):
    """
    An annotation dataset enabled on a workspace
    """

    __tablename__ = "artifact"
    __table_args__ = (UniqueConstraint("workspace_id", "object_path"),)

    workspace_id = Column(
        UUID(as_uuid=True), ForeignKey("workspace.id"), nullable=False
    )
    object_path = Column(String, nullable=False)
    object_name = Column(String, nullable=False)
    object_revision_date = Column(DateTime)
    name = Column(String, nullable=False)
    complete = Column(Boolean, nullable=False, default=False)

    workspace = relationship(Workspace, back_populates="annotation_datasets")
