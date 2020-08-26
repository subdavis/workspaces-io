import datetime
import enum
import uuid

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import (Boolean, Column, DateTime, Enum, ForeignKey, Integer,
                        String, Table)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from .database import Base
from .schemas import ShareType

# Many to Many
# https://docs.sqlalchemy.org/en/13/orm/basic_relationships.html#many-to-many
workspace_s3token_association_table = Table(
    "workspace_s3token_association_table",
    Base.metadata,
    Column(
        "workspace_id", UUID(as_uuid=True), ForeignKey("workspace.id"), nullable=True
    ),
    Column(
        "s3token_id", UUID(as_uuid=True), ForeignKey("minio_token.id"), nullable=False
    ),
)


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
    tokens = relationship(
        "S3Token",
        secondary=workspace_s3token_association_table,
        back_populates="workspaces",
    )


class Share(BaseModel):
    """
    A share is a mechanism for workspaces to be shared
    among users.  Both public and private workspaces may be
    shared with other entities.
    """

    __tablename__ = "share"
    __table_args__ = (UniqueConstraint("workspace_id", "creator_id", "sharee_id"),)

    workspace_id = Column(
        UUID(as_uuid=True), ForeignKey("workspace.id"), nullable=False
    )
    creator_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    sharee_id = Column(UUID(as_uuid=True), nullable=False)
    permission = Column(Enum(ShareType), nullable=False)
    expiration = Column(DateTime, nullable=True)

    sharee = relationship(User, backref="shares")
    creator = relationship(User, backref="shares_created")
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

    access_key_id = Column(String, nullable=False)
    secret_access_key = Column(String, nullable=False)
    session_token = Column(String, nullable=False)
    expiration = Column(
        DateTime,
        default=datetime.datetime.now() + datetime.timedelta(days=7),
        nullable=False,
    )
    policy = Column(JSONB, nullable=False)
    bucket = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)

    owner = relationship(User, backref="s3_tokens")
    workspaces = relationship(
        "Workspace",
        secondary=workspace_s3token_association_table,
        back_populates="tokens",
    )
