import boto3
from sqlalchemy.sql import text
from sqlalchemy.orm import Session

from . import models, schemas, settings, s3utils


def on_after_register(db: Session, user: schemas.UserDB):
    print(f"User {user.id} has registered.")


def on_after_forgot_password(db: Session, user: schemas.UserDB):
    print(f"User {user.id} has forgot their password")


def workspace_list(
    db: Session,
    requester: schemas.UserDB,
):
    query = """
    SELECT
        workspace.public as public,
        workspace.bucket as bucket,
        workspace.name as name,
        workspace.owner_id as owner_id,
        share.permission as permission,
    FROM workspace, share
    WHERE workspace.id = share.workspace_id
        AND (workspace.owner_id = :owner_id
            OR share.sharee_id = :owner_id)
    """
    return db.engine.execute(text(query), owner_id=requester.id)


def workspace_create(
    db: Session,
    b3: boto3.Session,
    workspace: schemas.WorkspaceCreate,
    owner: schemas.UserDB,
):
    db_workspace = models.Workspace(
        **workspace.dict(), owner_id=owner.id, bucket=settings.DEFAULT_BUCKET
    )
    db.add(db_workspace)
    key = s3utils.getWorkspaceKey(workspace, owner.username)

    def makeWorkspace():
        b3.put_object(ACL="private", Body=b"", Bucket=db_workspace.bucket, Key=key)

    def makeBucket():
        b3.crete_bucket(ACL='private', Bucket=db_workspace.bucket)
    
    try:
        makeWorkspace()
    except b3.exceptions.NoSuchBucketException:
        makeBucket()
        makeWorkspace()

    db.commit()
    db.refresh(db_workspace)
    return db_workspace
