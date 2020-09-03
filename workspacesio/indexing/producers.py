"""
Produce sources for indexing given some root
"""
import posixpath
from typing import Iterable, Union

import minio

from workspacesio import depends, schemas

clientCache = depends.Boto3ClientCache()


def minio_list_root_children(
    node: schemas.StorageNodeOperator, root: schemas.WorkspaceRootDB
) -> dict:
    b3client = clientCache.get_minio_sdk_client(node)
    print(root.bucket, root.base_path)
    return b3client.list_objects_v2(root.bucket, prefix=(root.base_path or ""))


def minio_recursive_generate_objects(
    node: schemas.StorageNodeOperator,
    root: schemas.WorkspaceRootDB,
    workspace: schemas.WorkspaceDB,
) -> Iterable[minio.Object]:
    b3client = clientCache.get_minio_sdk_client(node)
    start_after: Union[str, None] = ""
    bucket = root.bucket
    prefix = posixpath.join(root.base_path, workspace.base_path or "")
    while start_after is not None:
        object_list = b3client.list_objects_v2(bucket, prefix=prefix, recursive=True,)
        for obj in object_list:
            yield obj
        start_after = None
