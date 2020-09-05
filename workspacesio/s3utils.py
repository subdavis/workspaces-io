"""
Helper functions for working with S3 and STS
"""
import posixpath
import uuid
from typing import List, Optional, Set, Tuple, Union

from . import models, schemas, settings


def sanitize(name: str):
    # TODO
    return name


def getWorkspaceKey(workspace: Union[models.Workspace, schemas.WorkspaceDB]):
    """
    Determine full object prefix for a given workspace
    """
    inner_path = workspace.base_path or posixpath.join(
        workspace.owner.username, sanitize(workspace.name)
    )
    return posixpath.join(workspace.root.base_path, inner_path,).strip("/")


def makeRoleSessionName(user: schemas.UserBase, workspace: Optional[models.Workspace]):
    return f"{user.id}::{workspace}"


def makePolicy(
    user: schemas.UserBase,
    workspaces: List[models.Workspace],
    foreign_workspaces: List[Tuple[models.Workspace, Optional[models.Share]]],
):
    """
    Make a policy for the given user to access s3 based on
    https://aws.amazon.com/premiumsupport/knowledge-center/s3-folder-user-access/

    All workspaces passed in MUST be part of the same storage node.

    :param user: the policyholder
    :param workspaces: only add these to policy if they're public or owned by user
    :param foregin_workspaces: add these according to their shares
    """
    if len(workspaces) == 0 and len(foreign_workspaces) == 0:
        raise ValueError("No workspaces found")

    # Some sets to prevent duplicate policies from being added
    # such as if two different public workspaces come from the same root
    node_id: Union[uuid.UUID, None] = None
    root_ids: Set[uuid.UUID] = set()
    workspace_ids: Set[uuid.UUID] = set()
    statements: List[dict] = [
        {
            "Action": ["s3:ListAllMyBuckets", "s3:GetBucketLocation"],
            "Effect": "Allow",
            "Resource": ["arn:aws:s3:::*"],
        }
    ]
    for w in workspaces:
        if node_id is not None and w.root.storage_node.id != node_id:
            raise ValueError("Multiple nodes found in workspace list")
        elif node_id is None:
            node_id = w.root.storage_node.id
        if w.root_id in root_ids:
            continue
        root_ids.add(w.root_id)
        bucket = w.root.bucket
        resourceBase = f"arn:aws:s3:::{bucket}"
        workspacekey = getWorkspaceKey(w)
        usernamekey = workspacekey.rstrip(w.name)

        if w.root.root_type == schemas.RootType.PUBLIC:
            basepath = w.root.base_path or ""
            statements += [
                {
                    "Action": ["s3:ListBucket"],
                    "Effect": "Allow",
                    "Resource": [resourceBase],
                    "Condition": {
                        "StringLike": {"s3:prefix": posixpath.join(basepath, "*")}
                    },
                },
                {
                    "Effect": "Allow",
                    "Action": ["s3:GetObject"],
                    "Resource": [posixpath.join(resourceBase, basepath, "*")],
                },
            ]
            if w.owner_id == user.id:
                statements.append(
                    {
                        "Effect": "Allow",
                        "Action": ["s3:*"],
                        "Resource": [posixpath.join(resourceBase, usernamekey, "*")],
                    }
                )
        elif w.root.root_type == schemas.RootType.PRIVATE:
            statements += [
                {
                    "Action": ["s3:ListBucket"],
                    "Effect": "Allow",
                    "Resource": [resourceBase],
                    "Condition": {
                        "StringLike": {"s3:prefix": usernamekey, "s3:delimiter": "/",}
                    },
                },
                {
                    "Action": ["s3:ListBucket"],
                    "Effect": "Allow",
                    "Resource": [resourceBase],
                    "Condition": {
                        "StringLike": {"s3:prefix": posixpath.join(usernamekey, "*"),}
                    },
                },
                {
                    "Effect": "Allow",
                    "Action": ["s3:*"],
                    "Resource": [posixpath.join(resourceBase, usernamekey, "*"),],
                },
            ]
    for w, share in foreign_workspaces:
        if node_id is not None and w.root.storage_node.id != node_id:
            raise ValueError("Multiple nodes found in workspace list")
        elif node_id is None:
            node_id = w.root.storage_node.id
        bucket = w.root.bucket
        resourceBase = f"arn:aws:s3:::{bucket}"
        workspacekey = getWorkspaceKey(w)
        statements += [
            {
                "Action": ["s3:ListBucket"],
                "Effect": "Allow",
                "Resource": [resourceBase],
                "Condition": {
                    "StringLike": {"s3:prefix": workspacekey, "s3:delimiter": "/"}
                },
            },
            {
                "Action": ["s3:ListBucket"],
                "Effect": "Allow",
                "Resource": [resourceBase],
                "Condition": {
                    "StringLike": {"s3:prefix": posixpath.join(workspacekey, "*")}
                },
            },
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject"],
                "Resource": [posixpath.join(resourceBase, workspacekey, "*")],
            },
        ]
        if share is not None:
            if (
                share.permission is schemas.ShareType.READWRITE
                or share.permission is schemas.ShareType.OWN
            ):
                statements.append(
                    {
                        "Effect": "Allow",
                        "Action": ["s3:PutObject", "s3:DeleteObject"],
                        "Resource": [posixpath.join(resourceBase, workspacekey, "*")],
                    }
                )
        if share is None and w.owner_id == user.id:
            statements.append(
                {
                    "Effect": "Allow",
                    "Action": ["s3:PutObject", "s3:DeleteObject"],
                    "Resource": [posixpath.join(resourceBase, workspacekey, "*")],
                }
            )

    return {
        "Version": "2012-10-17",
        "Statement": statements,
    }


def makeEmptyPolicy():
    return {
        "Version": "2012-10-17",
        "Statement": [],
    }
