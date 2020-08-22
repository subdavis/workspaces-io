import datetime
import json
from typing import Optional, Union, List
import uuid

import boto3
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text
from sqlalchemy.orm import Session

from . import models, schemas, settings, s3utils


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
    db_workspace = models.Workspace(
        **workspace.dict(), owner_id=owner.id, bucket=settings.DEFAULT_BUCKET
    )
    db.add(db_workspace)
    key = s3utils.getWorkspaceKey(db_workspace)

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
    existing: Union[models.S3Token, None] = (
        db.query(models.S3Token)
        .filter(
            and_(
                models.S3Token.workspace_id == token.workspace_id,
                models.S3Token.owner_id == requester.id,
            )
        )
        .first()
    )

    if existing and existing.expiration > datetime.datetime.utcnow():
        return existing
    else:
        workspace = db.query(models.Workspace).get(token.workspace_id)
        token_db = existing or models.S3Token(**token.dict())
        db.add(token_db)
        new_token = b3.assume_role(
            RoleArn="arn:xxx:xxx:xxx:xxxx",  # Not meaningful for Minio
            RoleSessionName="foo",  # Not meaningful for Minio
            Policy=json.dumps(s3utils.makePolicy(requester, workspace)),
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


def share_list(
    db: Session, user: schemas.UserDB,
):
    """List shared-by and shared-with user"""
    return db.query(models.Share).filter(models.Share.creator_id == user.id).all()
