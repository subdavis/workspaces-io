"""
Artifact utils
"""
import posixpath
from typing import Generator, Iterable, List, Optional, Tuple, TypeVar, Union

import minio

from workspacesio import depends, s3utils, schemas
from workspacesio.indexing import schemas as indexing_schemas
from workspacesio.indexing import video

clientCache = depends.Boto3ClientCache()


def get_object_artifacts_for_node(
    node: schemas.StorageNodeOperator,
    root: schemas.WorkspaceRootDB,
    workspace: schemas.WorkspaceDB,
    obj: minio.Object,
) -> dict:
    """Artifacts directly from MinIO"""
    path = s3utils.getWorkspaceKey(workspace, root)
    prefix = posixpath.join(root.base_path, "")  # add trailing slash
    return clientCache.get_minio_sdk_client(node).list_objects_v2(
        root.bucket, prefix=prefix
    )
