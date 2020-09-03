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


def getWorkspaceKey(workspace: models.Workspace):
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
    foreign_workspaces: List[Tuple[models.Workspace, models.Share]],
):
    """
    Make a policy for the given user to access s3 based on
    https://aws.amazon.com/premiumsupport/knowledge-center/s3-folder-user-access/

    All workspaces passed in MUST be part of the same storage node.

    :param user: the policyholder
    :param workspaces: only add these to policy if they're public or owned by user
    :param foregin_workspaces: add these according to their shares
    """
    if len(workspaces) == 0:
        raise ValueError("No workspaces found")

    # Some sets to prevent duplicate policies from being added
    # such as if two different public workspaces come from the same root
    node_ids: Set[uuid.UUID] = {workspaces[0].root.storage_node.id}
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
        if not w.root.storage_node.id in node_ids:
            raise ValueError("Multiple nodes found in workspace list")
        if w.root_id in root_ids:
            continue
        root_ids.add(w.root_id)
        bucket = w.root.bucket
        resourceBase = f"arn:aws:s3:::{bucket}"

        if w.root.root_type == schemas.RootType.PUBLIC:
            basepath = w.root.base_path or ""
            statements += [
                # {
                #     "Action": ["s3:ListBucket"],
                #     "Effect": "Allow",
                #     "Resource": [resourceBase],
                #     "Condition": {
                #         "StringLike": {"s3:prefix": "public", "s3:delimiter": "/"}
                #     },
                # },
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
                        "Resource": [
                            posixpath.join(resourceBase, basepath, user.username, "*")
                        ],
                    }
                )
        elif w.root.root_type in [schemas.RootType.PRIVATE, schemas.RootType.UNMANAGED]:
            inner_path = user.username
            if w.root.root_type == schemas.RootType.UNMANAGED:
                inner_path = w.base_path or ""
            # this is a public workspace, grant read on public root
            statements += [
                {
                    "Action": ["s3:ListBucket"],
                    "Effect": "Allow",
                    "Resource": [resourceBase],
                    "Condition": {
                        "StringLike": {
                            "s3:prefix": posixpath.join(w.root.base_path, inner_path),
                            "s3:delimiter": "/",
                        }
                    },
                },
                {
                    "Action": ["s3:ListBucket"],
                    "Effect": "Allow",
                    "Resource": [resourceBase],
                    "Condition": {
                        "StringLike": {
                            "s3:prefix": posixpath.join(
                                w.root.base_path, inner_path, "*"
                            ),
                        }
                    },
                },
                {
                    "Effect": "Allow",
                    "Action": ["s3:*"],
                    "Resource": [
                        posixpath.join(resourceBase, w.root.base_path, inner_path, "*"),
                    ],
                },
            ]
    for w, share in foreign_workspaces:
        if not w.root.storage_node.id in node_ids:
            raise ValueError("Multiple nodes found in workspace list")
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

    return {
        "Version": "2012-10-17",
        "Statement": statements,
    }


def makeEmptyPolicy():
    return {
        "Version": "2012-10-17",
        "Statement": [],
    }
