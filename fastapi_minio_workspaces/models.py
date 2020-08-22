import datetime
import enum
import uuid

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from .database import Base
from .schemas import ShareType


class BaseModel(AbstractConcreteBase, Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created = Column(DateTime, default=datetime.datetime.utcnow)


class User(Base, SQLAlchemyBaseUserTable):
    __tablename__ = "user"
    username = Column(String)


class Workspace(BaseModel):
    """
    A workspace is a directory-like ARN in s3.
    * public workspaces, that all system users can READ,
      arn:aws:s3:::{bucketname}/public/{user}/{name}
    * private workspaces, that only the owner can READ,
      arn:aws:s3:::{bucketname}/private/{user}/{name}

    READ/WRITE privileges to public and private workspaces
    can be shared among users.
    """

    __tablename__ = "workspace"
    # workspace names are unique per user
    __table_args__ = (UniqueConstraint("name", "owner_id"),)

    public = Column(Boolean, default=True, nullable=False)
    bucket = Column(String, nullable=False)
    name = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)

    owner = relationship(User, backref="workspaces")


class Share(BaseModel):
    """
    A share is a mechanism for workspaces to be shared
    among users.  Both public and private workspaces may be
    shared with other entities.
    """

    __tablename__ = "share"

    workspace_id = Column(
        UUID(as_uuid=True), ForeignKey("workspace.id"), nullable=False
    )
    creator_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    sharee_id = Column(UUID(as_uuid=True), nullable=False)
    permission = Column(Enum(ShareType), nullable=False)
    expiration = Column(DateTime, nullable=True)

    sharee = relationship(User, backref="shares")
    workspace = relationship(Workspace, backref="shares")


class S3Token(BaseModel):
    """
    There are two kinds of tokens that users might request
    * A general purpose token to use anything they own.
    * A specific workspace token for a single shared workspace.
      If a user needs concurrent access to many shared workspaces,
      they must have many outstanding tokens.
    """

    __tablename__ = "minio_token"
    # users may only have a single outstanding token for a workspace
    __table_args__ = (UniqueConstraint("workspace_id", "owner_id"),)

    access_key_id = Column(String)
    secret_access_key = Column(String)
    session_token = Column(String)
    expiration = Column(
        DateTime, default=datetime.datetime.now() + datetime.timedelta(days=7)
    )

    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspace.id"))
    owner_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))

    workspace = relationship(Workspace, backref="s3_tokens")
    owner = relationship(User, backref="s3_tokens")
