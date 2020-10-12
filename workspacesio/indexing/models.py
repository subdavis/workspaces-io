import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from workspacesio.models import BaseModel, Workspace, WorkspaceRoot


class RootIndex(BaseModel):
    """
    RootIndexes are enabled per-root.  To index a workspace, its root must have indexing
    enabled through the creation of an RootIndex.

    This is done because roots are control boundaries, so in order to subscribe to
    bucket notifications, it's most convenient for node operators to create a single
    event stream for each root.

    There may be many roots, and therefore many root indexes, but they will all
    funnel into the same index in elasticsearch.
    """

    __tablename__ = "root_index"
    __table_args__ = (UniqueConstraint("root_id", "index_type"),)

    root_id = Column(
        UUID(as_uuid=True), ForeignKey("workspace_root.id"), nullable=False
    )
    index_type = Column(String, nullable=False)

    root = relationship(WorkspaceRoot, back_populates="indexes")


class WorkspaceCrawlRound(BaseModel):
    """
    WorkspaceCrawlRound is the smallest unit of indexing work.  An entire workspace
    must be crawled before the process can begin again.  Crawl can happen in 2 distinct
    modes.

    Manual Mode

    A node operator can run a manual craw using the command line tool to re-index
    a workspace.  This will happen most often because objects on disk were changed through
    a mechanism unknown to MinIO/S3.

    Changes discovered during a crawl are considered current as of the begin time of the crawl.
    All objects discovered must have their index ID updated in elasticsearch.

    Streaming Mode

    In streaming mode, changes discovered are considered current as of the latest open or
    completed index.
    """

    __tablename__ = "workspace_crawl_round"

    workspace_id = Column(
        UUID(as_uuid=True), ForeignKey("workspace.id"), nullable=False
    )
    start_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    end_time = Column(DateTime, default=None, nullable=True)
    succeeded = Column(Boolean, default=False, nullable=False)
    last_indexed_key = Column(String, nullable=True)
    total_objects = Column(Integer, nullable=False, default=0)
    total_size = Column(Integer, nullable=False, default=0)

    workspace = relationship(Workspace, backref="crawl_rounds")
