"""
Helper functions for working with S3 and STS
"""
from typing import Optional

from . import models, schemas, settings


def sanitize(name: str):
    # TODO
    return name


def getWorkspaceKey(workspace: models.Workspace):
    """
    Determine object path for a given workspace
    """
    root = "public" if workspace.public else "private"
    return f"{root}/{workspace.owner.username}/{sanitize(workspace.name)}"


def makeRoleSessionName(user: schemas.UserDB, workspace: Optional[models.Workspace]):
    return f"{user.id}::{workspace}"


def makePolicy(user: schemas.UserDB, workspace: Optional[models.Workspace]):
    """
    Make a policy for the given user to access s3 based on
    https://aws.amazon.com/premiumsupport/knowledge-center/s3-folder-user-access/
    """
    resourceBase = f"arn:aws:s3:::{settings.DEFAULT_BUCKET}"
    statements = []
    if workspace is None:
        # This is a blanket user policy
        statements.append(
            {
                "Action": ["s3:ListAllMyBuckets", "s3:GetBucketLocation"],
                "Effect": "Allow",
                "Resource": ["arn:aws:s3:::*"],
            }
        )
        # General public access
        statements.append(
            {
                "Action": ["s3:ListBucket"],
                "Effect": "Allow",
                "Resource": [resourceBase],
                "Condition": {
                    "StringLike": {"s3:prefix": "public", "s3:delimiter": "/"}
                },
            }
        )
        statements.append(
            {
                "Action": ["s3:ListBucket"],
                "Effect": "Allow",
                "Resource": [resourceBase],
                "Condition": {"StringLike": {"s3:prefix": "public/*"}},
            }
        )
        statements.append(
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject"],
                "Resource": [f"{resourceBase}/public/*"],
            }
        )
        # Private user access
        statements.append(
            {
                "Action": ["s3:ListBucket"],
                "Effect": "Allow",
                "Resource": [resourceBase],
                "Condition": {
                    "StringLike": {
                        "s3:prefix": f"private/{user.username}",
                        "s3:delimiter": "/",
                    }
                },
            }
        )
        statements.append(
            {
                "Action": ["s3:ListBucket"],
                "Effect": "Allow",
                "Resource": [resourceBase],
                "Condition": {
                    "StringLike": {"s3:prefix": f"private/{user.username}/*"}
                },
            }
        )
        statements.append(
            {
                "Effect": "Allow",
                "Action": ["s3:*"],
                "Resource": [f"{resourceBase}/private/{user.username}/*"],
            }
        )
    else:
        # This is a specific workspace share policy
        # TODO
        pass

    return {
        "Version": "2012-10-17",
        "Statement": statements,
    }


def makeEmptyPolicy():
    return {
        "Version": "2012-10-17",
        "Statement": [],
    }
