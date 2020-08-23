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
    return f"{root}/{workspace.owner.username}/{sanitize(workspace.name)}/"


def makeRoleSessionName(user: schemas.UserDB, workspace: Optional[models.Workspace]):
    return f"{user.id}::{workspace}"


def makePolicy(user: schemas.UserDB, workspace: Optional[models.Workspace]):
    """
    Make a policy for the given user to access s4
    """
    resourceBase = f"arn:aws:s3:::{settings.DEFAULT_BUCKET}"
    resouces = []
    if workspace is None:
        # This is a blanket user policy
        resouces = [
            f"{resourceBase}/public/{user.username}/*",
            f"{resourceBase}/private/{user.username}/*",
        ]
    else:
        # This is a specific workspace share policy
        workspaceKey = getWorkspaceKey(workspace)
        resources = [f"{resourceBase}/{workspaceKey}*"]
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": ["s3:GetObject", "s3:PutObject"],
                "Effect": "Allow",
                "Resource": resouces,
            },
        ],
    }


def makeEmptyPolicy():
    return {
        "Version": "2012-10-17",
        "Statement": [],
    }
