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

from workspacesio.schemas import DBBaseModel, WorkspaceRootDB


class IndexDocumentBase(BaseModel):
    time: datetime.datetime
    size: Optional[int]
    eTag: Optional[str]
    path: str
    extension: str


class IndexDocument(IndexDocumentBase):
    workspace_id: uuid.UUID
    workspace_name: str
    owner_id: uuid.UUID
    owner_name: str
    bucket: str
    server: str
    root_path: str
    root_id: uuid.UUID
    user_shares: List[uuid.UUID]


class IndexBase(BaseModel):
    index_type: str
    root_id: uuid.UUID


class IndexCreate(IndexBase):
    pass


class IndexDB(DBBaseModel, IndexBase):
    root: WorkspaceRootDB


class IndexBulkAdd(BaseModel):
    """Bulk add records from a workspace into the index"""

    documents: List[IndexDocumentBase]
    workspace_id: uuid.UUID


class IndexBulkAddedResponse(BaseModel):
    index: IndexDB
    count: int


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


class ElasticUpsertIndexDocument(BaseModel):
    doc: IndexDocument
    doc_as_upsert = True


INDEX_DOCUMENT_MAPPING = {
    "properties": {
        "time": {"type": "date"},
        "size": {"type": "double"},
        "eTag": {"type": "text"},
        "workspace_id": {
            "type": "keyword",
        },
        "workspace_name": {"type": "keyword"},
        "owner_id": {"type": "keyword"},
        "owner_name": {"type": "keyword"},
        "bucket": {"type": "keyword"},
        "server": {"type": "keyword"},
        "root_path": {"type": "text"},
        "root_id": {"type": "keyword"},
        "path": {"type": "search_as_you_type"},
        "extension": {"type": "keyword"},
        "user_shares": {"type": "keyword"},
    }
}
