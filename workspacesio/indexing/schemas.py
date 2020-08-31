"""
Set of schemas that represent POST body of minio/s3 bucket event notifications.
Minio is slightly inconsistent in its specific schema.  These schemas seek
to work for both s3 and minio.

https://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html
https://github.com/minio/minio-dotnet/issues/332
"""
import datetime
import uuid
from typing import List, Optional

from pydantic import BaseModel
from workspacesio.schemas import DBBaseModel


class IndexBase(BaseModel):
    s3_api_url: str
    s3_bucket: str
    s3_root: str
    index_type: str


class IndexCreate(IndexBase):
    pass


class IndexDB(DBBaseModel, IndexBase):
    s3_root: str


class IndexCreateResponse(BaseModel):
    commands: List[str]
    index: IndexDB


class EventUserIdentity(BaseModel):
    principalId: str


class Bucket(BaseModel):
    name: str
    ownerIdentity: EventUserIdentity
    arn: str


class EventObject(BaseModel):
    key: str
    size: Optional[int]
    eTag: Optional[str]
    contentType: Optional[str]
    sequencer: str


class S3Event(BaseModel):
    s3SchemaVersion: str
    configurationId: str
    bucket: Bucket
    object: EventObject


class EventNotificationRecord(BaseModel):
    awsRegion: str
    eventName: str
    eventVersion: str
    eventSource: str
    eventTime: datetime.datetime
    userIdentity: EventUserIdentity
    requestParameters: dict
    responseElements: dict
    s3: S3Event


class BucketEventNotification(BaseModel):
    Records: List[EventNotificationRecord]
    EventName: Optional[str]
    Key: Optional[str]


class IndexDocument(BaseModel):
    time: datetime.datetime
    size: Optional[int]
    eTag: str
    workspace_id: uuid.UUID
    workspace_name: str
    owner_id: uuid.UUID
    owner_name: str
    bucket: str
    server: str
    root: str
    path: str
    user_shares: List[uuid.UUID]


class UpsertIndexDocument(BaseModel):
    doc: IndexDocument
    doc_as_upsert = True


INDEX_DOCUMENT_MAPPING = {
    "properties": {
        "time": {"type": "date"},
        "size": {"type": "double"},
        "eTag": {"type": "text"},
        "workspace_id": {"type": "text"},
        "workspace_name": {"type": "text"},
        "owner_id": {"type": "text"},
        "owner_name": {"type": "text"},
        "bucket": {"type": "text"},
        "server": {"type": "text"},
        "root": {"type": "text"},
        "path": {"type": "text"},
        "user_shares": {"type": "text"},
    }
}
