"""
Produce sources for indexing given some root
"""
import posixpath
from typing import Iterable, List, Union

import minio

from workspacesio import depends, s3utils, schemas
from workspacesio.indexing import schemas as indexing_schemas

clientCache = depends.Boto3ClientCache()


def minio_list_root_children(
    node: schemas.StorageNodeOperator, root: schemas.WorkspaceRootDB
) -> dict:
    """Get direct children from a root"""
    return clientCache.get_minio_sdk_client(node).list_objects_v2(
        root.bucket, prefix=(root.base_path or "")
    )


def minio_recursive_generate_objects(
    node: schemas.StorageNodeOperator,
    root: schemas.WorkspaceRootDB,
    workspace: schemas.WorkspaceDB,
) -> Iterable[minio.Object]:
    """Generate a flat list of minio objects from a workspace"""
    b3client = clientCache.get_minio_sdk_client(node)
    bucket = root.bucket
    prefix = posixpath.join(root.base_path, s3utils.getWorkspaceKey(workspace))
    return b3client.list_objects_v2(bucket, prefix=prefix, recursive=True,)


def minio_buffer_objects(
    objects: List[minio.Object], buffer_size=10
) -> Iterable[minio.Object]:
    """Return small batches of objects"""
    index = 0
    buf: List[minio.Object] = []
    for o in objects:
        if index < buffer_size:
            buf.append(o)
            index += 1
        else:
            yield buf
            index = 0
            buf = []
    if index != 0:
        yield buf


def minio_transform_object(
    workspace: schemas.WorkspaceDB, root: schemas.WorkspaceRootDB, obj: minio.Object
) -> indexing_schemas.IndexDocumentBase:
    """Turn an object into a index document"""
    common = s3utils.getWorkspaceKey(workspace)
    assert (
        posixpath.commonprefix([common, obj.object_name]) is common
    ), f"{common} not in {obj.object_name}"
    inner = obj.object_name.lstrip(common)
    return indexing_schemas.IndexDocumentBase(
        time=obj.last_modified,
        size=obj.size,
        etag=obj.etag,
        path=inner,
        extension=posixpath.splitext(inner)[-1],
    )
