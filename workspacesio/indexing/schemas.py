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

from workspacesio.schemas import DBBaseModel, WorkspaceDB, WorkspaceRootDB


INDEX_DOCUMENT_MAPPING = {
    "properties": {
        # Base
        "time": {"type": "date"},
        "size": {"type": "double"},
        "eTag": {"type": "text"},
        "extension": {"type": "keyword"},
        "content_type": {"type": "keyword"},
        "text": {"type": "search_as_you_type"},
        "tag": {"type": "keyword"},
        # Required
        "workspace_id": {
            "type": "keyword",
        },
        "workspace_name": {"type": "keyword"},
        "owner_id": {"type": "keyword"},
        "owner_name": {"type": "keyword"},
        "bucket": {"type": "keyword"},
        "server": {"type": "keyword"},
        "root_path": {"type": "text"},
        "workspace_base_path": {"type": "text"},
        "last_seen_crawl_id": {"type": "keyword"},
        "root_id": {"type": "keyword"},
        "path": {"type": "text"},
        "filename": {"type": "text"},
        "user_shares": {"type": "keyword"},
        # Video
        "codec_tag_string": {"type": "keyword"},
        "width": {"type": "double"},
        "height": {"type": "double"},
        "r_frame_rate": {"type": "keyword"},
        "bit_rate": {"type": "double"},
        "duration_ts": {"type": "double"},
        "duration_sec": {"type": "double"},
        "format_name": {"type": "keyword"},
    }
}


class ProducerError(RuntimeError):
    pass


class IndexDocumentBase(BaseModel):
    """
    The main index document.  Any metadata that can apply to an entire object
    probably belongs in this schema.  It is intended as a union of all single-file
    metadata.  Elastic supports a lot of fields, so this will be fine unless we get into
    the mid hundreds.
    """

    # time of last update.  Note that through s3, creation time is not available
    time: datetime.datetime
    # size in bytes
    size: Optional[int]
    # minio/s3 eTag
    eTag: Optional[str]
    # path is the inner path starting at the workspace boundary
    path: str
    # object name is the file name alone
    filename: str
    # extension is the final extension
    extension: str
    # MIME content type
    content_type: Optional[str]
    # plaintext object contents if utf-8 encodeable
    text: Optional[str]
    # tag unused so far
    tag: Optional[str]

    # Optional Video Metadata
    codec_tag_string: Optional[str]
    width: Optional[int]
    height: Optional[int]
    r_frame_rate: Optional[str]
    bit_rate: Optional[str]
    duration_ts: Optional[int]
    duration_sec: Optional[str]
    format_name: Optional[str]
    # Optional Image Metadata
    # Optional Tabular Metadata
    # Optional Audio Metadata


class IndexDocument(IndexDocumentBase):
    """
    Additional tags that every object gets.  These will be assigned by the server
    if the bulk ingest endpoint is used.
    """

    workspace_id: uuid.UUID
    workspace_name: str
    owner_id: uuid.UUID
    owner_name: str
    bucket: str
    server: str
    root_path: str
    workspace_base_path: str
    last_seen_crawl_id: uuid.UUID
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
    last_indexed_key: str
    succeeded: Optional[bool]


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


class WorkspaceCrawlRoundBase(BaseModel):
    worksapce_id: uuid.UUID
    start_time: datetime.datetime
    succeeded: bool


class WorkspaceCrawlRoundDB(DBBaseModel, WorkspaceCrawlRoundBase):
    end_time: Optional[datetime.datetime]
    last_indexed_key: Optional[str]
    total_objects: int
    total_size: int
    workspace: WorkspaceDB
