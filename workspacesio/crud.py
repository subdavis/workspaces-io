import datetime
import json
import uuid
from typing import List, Optional, Tuple, Union

import boto3
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import all_, and_, func, or_
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

    @app.exception_handler(ValueError)
    async def value_exception_handler(r: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"message": str(exc)})


def on_after_register(db: Session, user: schemas.UserDB):
    print(f"User {user.id} has registered.")


def on_after_forgot_password(db: Session, user: schemas.UserDB):
    print(f"User {user.id} has forgot their password")


def workspace_list(
    db: Session, requester: schemas.UserDB, name: Optional[str] = None
) -> List[models.Workspace]:
    """Show workspaces that the requester owns or has a share for"""
    q = (
        db.query(models.Workspace)
        .outerjoin(models.Share, models.Share.workspace_id == models.Workspace.id)
        .filter(
            or_(
                models.Workspace.owner_id == requester.id,
                models.Share.sharee_id == requester.id,
            )
        )
    )
    if name is not None:
        q = q.filter(models.Workspace.name == name)
    return q.all()


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
    existing: Optional[models.S3Token] = (
        # https://stackoverflow.com/questions/11468572/postgresql-where-all-in-array
        # jesus helped me write this query
        db.query(models.S3Token)
        .join(models.S3Token.workspaces)
        .filter(
            and_(
                models.Workspace.id.in_(token.workspaces),
                models.S3Token.owner_id == requester.id,
            )
        )
        .group_by(models.S3Token.id)
        .having(func.count("*") == len(token.workspaces))
        .first()
    )

    if existing and existing.expiration > datetime.datetime.utcnow():
        return existing
    else:
        workspaces: models.Workspace = db.query(models.Workspace).filter(
            models.Workspace.id.in_(token.workspaces)
        ).all()
        policies: List[Tuple[Union[models.Workspace, None], schemas.ShareType]] = []

        for w in workspaces:
            if w.owner_id != requester.id:
                share: models.Share = db.query(models.Share).filter(
                    and_(
                        models.Share.workspace_id == w.id,
                        models.Share.sharee_id == requester.id,
                    )
                ).first()
                if share:
                    policies.append((w, share.permission))
                else:
                    raise PermissionError(
                        f"User {requester.username} is not permitted to access {w.name}"
                    )
            else:
                policies.append((None, schemas.ShareType.OWN))
        # TODO: give users the ability to set their own default bucket
        bucket = settings.DEFAULT_BUCKET
        policy = s3utils.makePolicy(requester, bucket, policies)
        token_args = dict(
            owner_id=requester.id, policy={}, bucket="foo", workspaces=workspaces,
        )
        new_token = b3.assume_role(
            RoleArn="arn:xxx:xxx:xxx:xxxx",  # Not meaningful for Minio
            RoleSessionName=str(requester.id),  # Not meaningful for Minio
            Policy=json.dumps(policy),
            DurationSeconds=3600,
        )
        token_db = existing or models.S3Token(**token_args)
        token_db.access_key_id = new_token["Credentials"]["AccessKeyId"]
        token_db.secret_access_key = new_token["Credentials"]["SecretAccessKey"]
        token_db.session_token = new_token["Credentials"]["SessionToken"]
        token_db.expiration = new_token["Credentials"]["Expiration"]
        db.add(token_db)
        db.commit()
        return token_db


def token_revoke(db: Session, token_id: uuid.UUID):
    """
    Remove token from DB.  Outstanding tokens in AWS/MinIO will continue
    to function until they expire naturally
    """
    db.delete(db.query(models.S3Token).get_or_404(token_id))
    db.commit()


def token_search(
    db: Session,
    b3: boto3.Session,
    requester: schemas.UserDB,
    terms: List[schemas.S3TokenSearch],
) -> schemas.S3TokenSearchResponse:
    """Search for a set of credentials that satisfy the terms"""
    workspaces: List[models.Workspace] = []
    workspace_ids: List[Union[str, None]] = []
    for term in terms:
        if term.workspace_name is not None:
            matches: List[models.Workspace] = workspace_list(
                db, requester, name=term.workspace_name
            )
            if len(matches) == 1:
                workspaces.append(matches[0])
                workspace_ids.append(matches[0].id)
            elif len(matches) > 1:
                raise RuntimeError("Unsupported")
            else:
                raise ValueError(f"No matches found for {term.workspace_name}")
        else:
            workspace_ids.append(None)
    token = token_create(
        db, b3, requester, schemas.S3TokenCreate(workspaces=workspace_ids)
    )
    return schemas.S3TokenSearchResponse(token=token, workspaces=workspaces)


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
