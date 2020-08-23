import datetime
import json
import uuid
from typing import List, Optional, Union

import boto3
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from . import models, s3utils, schemas, settings


def register_handlers(app: FastAPI):
    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(r: Request, exc: IntegrityError):
        return JSONResponse(status_code=409, content={"message": "Integrity Error"})

    @app.exception_handler(PermissionError)
    async def permissions_exception_handler(r: Request, exc: PermissionError):
        return JSONResponse(status_code=403, content={"message": str(exc)})


def on_after_register(db: Session, user: schemas.UserDB):
    print(f"User {user.id} has registered.")


def on_after_forgot_password(db: Session, user: schemas.UserDB):
    print(f"User {user.id} has forgot their password")


def workspace_list(
    db: Session, requester: schemas.UserDB,
) -> List[schemas.WorkspaceListItem]:
    """Show workspaces that the requester owns or has a share for"""
    query = """
    SELECT
        workspace.id as id,
        workspace.created as created,
        workspace.public as public,
        workspace.bucket as bucket,
        workspace.name as name,
        workspace.owner_id as owner_id,
        share.permission as permission
    FROM workspace
    LEFT JOIN share ON share.workspace_id = workspace.id
    WHERE workspace.owner_id = :owner_id
        OR share.sharee_id = :owner_id
    ORDER BY workspace.name;
    """
    results = db.execute(text(query), {"owner_id": requester.id,}).fetchall()
    return results


def workspace_create(
    db: Session,
    b3: boto3.Session,
    workspace: schemas.WorkspaceCreate,
    owner: schemas.UserDB,
) -> models.Workspace:
    """Create a workspace for owner, including an empty parent in s3"""
    db_owner = db.query(models.User).get_or_404(owner.id)
    db_workspace = models.Workspace(
        **workspace.dict(),
        owner_id=owner.id,
        bucket=settings.DEFAULT_BUCKET,
        owner=db_owner,
    )
    db.add(db_workspace)
    key = s3utils.getWorkspaceKey(db_workspace) + "/"

    def makeWorkspace():
        b3.put_object(ACL="private", Body=b"", Bucket=db_workspace.bucket, Key=key)

    def makeBucket():
        b3.create_bucket(ACL="private", Bucket=db_workspace.bucket)

    try:
        makeWorkspace()
    except b3.exceptions.NoSuchBucket:
        makeBucket()
        makeWorkspace()

    db.commit()
    return db_workspace


def token_list(db: Session, requester: schemas.UserDB) -> List[models.S3Token]:
    """List tokens for requester"""
    return (
        db.query(models.S3Token).filter(models.S3Token.owner_id == requester.id).all()
    )


def token_create(
    db: Session,
    b3: boto3.Session,
    requester: schemas.UserDB,
    token: schemas.S3TokenCreate,
) -> models.S3Token:
    """Create s3 sts token for requester if they have permissions"""
    if token.workspace_id:
        workspace: models.Workspace = db.query(models.Workspace).get_or_404(
            token.workspace_id
        )
        if workspace.owner_id == requester.id:
            target_workspace = None
            target_workspace_id = None
        else:
            target_workspace = workspace
            target_workspace_id = workspace.id

    existing: Union[models.S3Token, None] = (
        db.query(models.S3Token)
        .filter(
            and_(
                models.S3Token.workspace_id == target_workspace_id,
                models.S3Token.owner_id == requester.id,
            )
        )
        .first()
    )

    if existing and existing.expiration > datetime.datetime.utcnow():
        existing.workspace = workspace
        return existing
    else:
        permissions = schemas.ShareType.OWN
        if target_workspace_id:
            # TODO: base permissions on share
            pass
        token_args = dict(token.dict(), owner_id=requester.id)
        token_db = existing or models.S3Token(**token_args)
        db.add(token_db)
        new_token = b3.assume_role(
            RoleArn="arn:xxx:xxx:xxx:xxxx",  # Not meaningful for Minio
            RoleSessionName="foo",  # Not meaningful for Minio
            Policy=json.dumps(s3utils.makePolicy(requester, target_workspace)),
            DurationSeconds=3600,
        )
        token_db.access_key_id = new_token["Credentials"]["AccessKeyId"]
        token_db.secret_access_key = new_token["Credentials"]["SecretAccessKey"]
        token_db.session_token = new_token["Credentials"]["SessionToken"]
        token_db.expiration = new_token["Credentials"]["Expiration"]
        db.commit()
        return token_db


def token_revoke(db: Session, token_id: uuid.UUID):
    """
    Remove token from DB.  Outstanding tokens in AWS/MinIO will continue
    to function until they expire naturally
    """
    db.delete(db.query(models.S3Token).get_or_404(token_id))
    db.commit()


def share_create(
    db: Session, creator: schemas.UserDB, share: schemas.ShareCreate,
) -> models.Share:
    """
    Share share.workspace_id with share.sharee_id if creator has permission"""
    workspace_db: models.Workspace = db.query(models.Workspace).get_or_404(
        share.workspace_id
    )
    if workspace_db.owner_id != creator.id:
        raise PermissionError("Only the owner can share a workspace")
    # TODO: check if creator has an owner-type share themselves for workspace
    share_db = models.Share(**share.dict(), creator_id=creator.id)
    db.add(share_db)
    db.commit()
    return share_db


def share_list(db: Session, user: schemas.UserDB,) -> List[models.Share]:
    """List shared-by and shared-with user"""
    return (
        db.query(models.Share)
        .filter(
            or_(models.Share.creator_id == user.id, models.Share.sharee_id == user.id)
        )
        .all()
    )


def share_revoke(db: Session, share: schemas.ShareDB):
    # TODO: delete any tokens that depend on this share.
    pass


def share_update(db: Session, share: schemas.ShareUpdate):
    # TODO: delete any tokens that depend on this share.
    pass
