from sqlalchemy import (
    Column,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from workspacesio.models import BaseModel, WorkspaceRoot


class ElasticIndex(BaseModel):
    """
    Indexes are enabled per-root
    """

    __tablename__ = "elastic_index"
    __table_args__ = (UniqueConstraint("root_id", "index_type"),)

    root_id = Column(
        UUID(as_uuid=True), ForeignKey("workspace_root.id"), nullable=False
    )
    index_type = Column(String, nullable=False)

    root = relationship(WorkspaceRoot, back_populates="indexes")
