"""
Functions to generate policy documents for tokens
"""

from . import schemas


def sanitize(name: str):
    # TODO
    return name


def getWorkspaceKey(workspace: schemas.WorkspaceBase, username: str):
    root = 'public' if workspace.public else 'private'
    return f'{root}/{username}/{sanitize(workspace.name)}/'
