from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from workspacesio.models import BaseModel, Workspace

from .schemas import DatasetType


class AnnotationDataset(BaseModel):
    """
    An annotation dataset enabled on a workspace
    """

    __tablename__ = "annotation_dataset"
    __table_args__ = (UniqueConstraint("workspace_id", "media_path"),)

    workspace_id = Column(
        UUID(as_uuid=True), ForeignKey("workspace.id"), nullable=False
    )
    source_type = Column(Enum(DatasetType), nullable=False)
    fps = Column(Integer, nullable=False, default=30)
    # prefix inside workspace
    media_prefix = Column(String, nullable=False, default="")
    # filename if source type is video
    media_filename = Column(String, nullable=True, default=None)
    workspace = relationship(Workspace, ulates="annotation_datasets")


class Track(BaseModel):
    """
    A single track or detection belonging to an annotation dataset
    """

    __tablename__ = "annotation_track"
    __table_args__ = (UniqueConstraint("dataset_id", "track_id"),)

    dataset_id = Column(UUID(as_uuid=True), ForeignKey("annotation_dataset.id"))
    begin = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    track_id = Column(Integer, nullable=False)
    features = Column(JSONB, nullable=False)
    confidencePairs = Column(JSONB, nullable=False)
    attributes = Column(JSONB, nullable=True)
