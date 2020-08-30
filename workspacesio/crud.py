import datetime
import hashlib
import json
import os
import urllib.parse
import uuid
from typing import Dict, List, Optional, Tuple, Union

import boto3
import elasticsearch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import and_, any_, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from . import models, s3utils, schemas, settings
from .notifications import schemas as event_schemas


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


def on_after_register(db: Session, user: schemas.UserBase):
    print(f"User {user.id} has registered.")


def on_after_forgot_password(db: Session, user: schemas.UserBase):
    print(f"User {user.id} has forgot their password")


def match_terms(
    db: Session, requester: schemas.UserBase, term: str, sep: str = "/"
) -> Tuple[Optional[models.Workspace], Optional[str]]:
    """
    Annoying search criteria.
    """
    # Look for either 'workspacename' or 'username/workspacename'
    all_term_parts = term.strip(sep).split(sep)
    term_parts = all_term_parts
    user_id: Optional[uuid.UUID] = None

    if len(term_parts) >= 2:
        # if there are at least two terms, there's a chance
        # the first term is a username
        user: Optional[models.User] = db.query(models.User).filter(
            models.User.username.ilike(term_parts[0])
        ).first()
        if user is not None:
            user_id = user.id
            term_parts = term_parts[1:]
    if len(term_parts) >= 1:
        # if there's at least 1 remaining term,
        # it could be a workspace, and user_id could have been set
        matches: List[models.Workspace] = workspace_search(
            db, requester, name=term_parts[0], owner_id=user_id,
        )
        if len(matches) == 1:
            return matches[0], sep.join(term_parts[1:])
        elif len(matches) > 1:
            raise RuntimeError(f"Multiple workspace matches for {term_parts[0]}")
        else:
            # hail mary search, for when you found a user match for arg1
            # but there was no workspace for arg2, so maybe the arg1
            # match was a coincidence
            hail_mary_matches: List[models.Workspace] = workspace_search(
                db, requester, name=all_term_parts[0]
            )
            if len(matches) == 1:
                return matches[0], sep.join(all_term_parts[1:])
            elif len(matches) > 1:
                raise RuntimeError(f"Multiple workspace matches for {term_parts[0]}")
    return None, None


def node_search(db: Session) -> List[models.StorageNode]:
    return db.query(models.StorageNode).all()


def node_create(
    db: Session, creator: schemas.UserDB, params: schemas.StorageNodeCreate
) -> models.StorageNode:
    storage_node_db = models.StorageNode(**params.dict(), creator_id=creator.id)
    db.add(storage_node_db)
    db.commit()
    return storage_node_db


def root_search(db: Session, node_name: Optional[str]) -> List[models.WorkspaceRoot]:
    q = db.query(models.WorkspaceRoot)
    if node_name:
        q = q.filter(models.WorkspaceRoot.storage_node.has(name=node_name))
    return q.all()


def root_create(
    db: Session,
    b3: boto3.Session,
    creator: schemas.UserDB,
    params: schemas.WorkspaceRootCreate,
) -> models.WorkspaceRoot:
    node: models.StorageNode = (
        db.query(models.StorageNode)
        .filter(models.StorageNode.name == params.node_name)
        .first_or_404()
    )
    root_db = models.WorkspaceRoot(**params.dict(), node_id=node.id)
    b3.create_bucket(ACL="private", Bucket=root_db.bucket)
    db.add(root_db)
    db.commit()
    return root_db


def workspace_search(
    db: Session,
    requester: schemas.UserBase,
    name: Optional[str] = None,
    owner_id: Union[str, uuid.UUID, None] = None,
    public: Optional[bool] = False,
) -> List[models.Workspace]:
    """Show workspaces that are public,
    the requester owns, or has a share for, that meet the optional
    conditions"""
    q = db.query(models.Workspace).outerjoin(models.Share)
    main_filter = or_(
        models.Workspace.owner_id == requester.id,
        models.Share.sharee_id == requester.id,
    )
    if name is not None:
        # when name is specified, automatically include public
        q = q.filter(models.Workspace.name == name)
        public = True
    if public:
        main_filter = or_(
            main_filter, models.Workspace.root.has(root_type=schemas.RootType.PUBLIC)
        )
    q = q.filter(main_filter)
    if owner_id is not None:
        q = q.filter(models.Workspace.owner_id == owner_id)
    q = q.group_by(models.Workspace.id)

    return q.all()


def workspace_get(
    db: Session, user: schemas.UserDB, workspace_id: str
) -> Optional[models.Workspace]:
    ws: models.Workspace = db.query(models.Workspace).get_or_404(workspace_id)
    # TODO: check if user has permissions for workspace
    return ws


def workspace_create(
    db: Session,
    b3: boto3.Session,
    workspace: schemas.WorkspaceCreate,
    owner: schemas.UserBase,
) -> models.Workspace:
    """Create a workspace for owner, including an empty parent in s3"""
    db_owner: models.User = db.query(models.User).get_or_404(owner.id)
    # TODO: heuristic to decide which root to put a workspace in
    root_type: schemas.RootType = (
        schemas.RootType.PUBLIC if workspace.public else schemas.RootType.PRIVATE
    )
    db_root_q = db.query(models.WorkspaceRoot).filter(
        models.WorkspaceRoot.root_type == root_type
    )
    if workspace.node_name:
        db_root_q = db_root.filter(
            models.WorkspaceRoot.storage_node.has(name=workspace.node_name)
        )
    db_root: models.WorkspaceRoot = db_root_q.first_or_404()
    db_workspace = models.Workspace(
        name=workspace.name, owner_id=owner.id, root_id=db_root.id
    )
    db.add(db_workspace)
    key = s3utils.getWorkspaceKey(db_workspace) + "/"
    b3.put_object(ACL="private", Body=b"", Bucket=db_root.bucket, Key=key)
    db.commit()
    return db_workspace


def token_list(db: Session, requester: schemas.UserBase) -> List[models.S3Token]:
    """List tokens for requester"""
    return (
        db.query(models.S3Token)
        .filter(
            and_(
                models.S3Token.owner_id == requester.id,
                models.S3Token.expiration > datetime.datetime.utcnow(),
            )
        )
        .all()
    )


def token_create(
    db: Session,
    b3: boto3.Session,
    requester: schemas.UserBase,
    token: schemas.S3TokenCreate,
) -> Optional[models.S3Token]:
    """Create s3 sts token for requester if they have permissions"""
    # Find all workspaces in the query
    workspace_query_list: List[models.Workspace] = db.query(models.Workspace,).filter(
        models.Workspace.id.in_(token.workspaces)
    ).all()
    if len(workspace_query_list) == 0:
        return None

    foreign_workspaces = [
        w
        for w in workspace_query_list
        if (w.owner_id != requester.id and w.public == False)
    ]
    includes_owner_permissions = len(workspace_query_list) > len(foreign_workspaces)
    # TODO: group the workspace query list by server/bucket because a distinct S3 token
    # is needed for each member of that group.  For now, assume they all share a
    # common server and bucket

    query = (
        db.query(models.S3Token)
        .outerjoin(models.Workspace, models.S3Token.workspaces)
        .filter(
            and_(
                models.S3Token.owner_id == requester.id,
                or_(*[models.Workspace.id == w.id for w in foreign_workspaces]),
            )
        )
    )
    if includes_owner_permissions:
        query = query.filter(models.S3Token.includes_owner_permissions == True)
    # https://stackoverflow.com/questions/11468572/postgresql-where-all-in-array
    query = query.group_by(models.S3Token.id).having(
        func.count("*") >= len(foreign_workspaces)
    )
    existing: Optional[models.S3Token] = query.first()

    if existing and existing.expiration > datetime.datetime.utcnow():
        return existing
    else:
        policies: List[Tuple[Union[models.Workspace, None], schemas.ShareType]] = []
        for w in foreign_workspaces:
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
        if includes_owner_permissions:
            policies.append((None, schemas.ShareType.OWN))
        bucket = workspace_query_list[0].bucket
        policy = s3utils.makePolicy(requester, bucket, policies)
        token_args = dict(
            owner_id=requester.id,
            policy=policy,
            bucket=bucket,
            workspaces=foreign_workspaces,
            includes_owner_permissions=includes_owner_permissions,
        )
        new_token = b3.assume_role(
            RoleArn="arn:xxx:xxx:xxx:xxxx",  # Not meaningful for Minio
            RoleSessionName=str(requester.id),  # Not meaningful for Minio
            Policy=json.dumps(policy),
            DurationSeconds=900,
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


def token_revoke_all(db: Session, user: schemas.UserBase) -> int:
    """
    Remove all tokens from DB
    """
    all_tokens: List[models.S3Token] = db.query(models.S3Token).filter(
        models.S3Token.owner_id == user.id
    ).all()
    for t in all_tokens:
        t.workspaces.clear()
        db.delete(t)
    db.commit()
    return len(all_tokens)


def token_search(
    db: Session,
    b3: boto3.Session,
    requester: schemas.UserBase,
    search: schemas.S3TokenSearch,
) -> schemas.S3TokenSearchResponse:
    """Search for a set of credentials that satisfy the terms"""
    workspaces: Dict[str, schemas.S3TokenSearchResponseWorkspacePart] = {}
    token = None
    for path in search.search_terms:
        match, interior_path = match_terms(db, requester, path)
        if match:
            workspaces[path] = schemas.S3TokenSearchResponseWorkspacePart(
                workspace=match, path=interior_path,
            )
    workspace_id_list = [w.workspace.id for w in workspaces.values()]
    if len(workspace_id_list):
        token = token_create(
            db, b3, requester, schemas.S3TokenCreate(workspaces=workspace_id_list),
        )
    return schemas.S3TokenSearchResponse(token=token, workspaces=workspaces,)


def share_create(
    db: Session, creator: schemas.UserBase, share: schemas.ShareCreate,
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


def share_list(db: Session, user: schemas.UserBase,) -> List[models.Share]:
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


def index_create(
    db: Session, b3: boto3.Session, es: elasticsearch.Elasticsearch
) -> schemas.IndexCreateResponse:
    """Setup notifications and indexing for a root
    * Provide a command for the operator to create the notification stream
    * Verify that the index exists in elasticsearch
    * Insert or update an index record
    """

    public_index: Optional[models.ElasticIndex] = db.query(models.ElasticIndex).filter(
        models.ElasticIndex.public == True
    ).first()
    if public_index is None:
        public_index = models.ElasticIndex(
            public=True,
            s3_api_url="http://minio:9000",
            s3_bucket="fast",
            s3_root="public".lstrip("/"),
            index_type="default",
        )
        index_name = public_index.index_type
        db.add(public_index)
        db.flush()
        es.indices.create(
            index_name, body={"mappings": event_schemas.INDEX_DOCUMENT_MAPPING}
        )
        db.commit()
        db.refresh()
    # Right now, it's easiest to support webhooks
    commands = [
        # wehook ID should come from ROOT, not index.  You only want to subscribe to events once.
        f"mc admin config set ALIAS notify_webhook:{str(public_index.id)} endpoint=http://varrock:8000/api/minio/events",
        f"mc event add ALIAS/{public_index.s3_bucket} arn:minio:sqs::{str(public_index.id)}:webhook --prefix {public_index.s3_root} --event delete,put",
    ]
    return schemas.IndexCreateResponse(commands=commands, index=public_index)


def handle_bucket_event(
    db: Session,
    ec: elasticsearch.Elasticsearch,
    event: event_schemas.BucketEventNotification,
):
    # Find workspace for event
    bulk_operations = ""
    for record in event.Records:
        bucket = record.s3.bucket.name
        # TODO: find the root, which will give us the naming convention
        # for child buckets
        # For now, find the index
        object_key = urllib.parse.unquote(record.s3.object.key)
        parent_index: models.ElasticIndex = db.query(models.ElasticIndex).filter(
            func.strpos(models.ElasticIndex.s3_root, object_key) == 0
        ).first()
        if parent_index is None:
            raise ValueError(f"no index for object {object_key}")
        # TODO: skip the part where we extrapolate workspace name, assume it's {scope}/{user}/{workspace}
        key_parts = object_key.split("/")
        scope = key_parts[0]
        user_name = key_parts[1]
        workspace_name = key_parts[2]
        workspace_inner_path = "/".join(key_parts[3:])
        # TODO: server and root will have to be joined.
        resource_owner: models.User = db.query(models.User).filter(
            models.User.username == user_name
        ).first()
        if resource_owner is None:
            raise ValueError(f"no owner found for object {object_key}")
        workspace: models.Workspace = db.query(models.Workspace).filter(
            and_(
                models.Workspace.name == workspace_name,
                models.Workspace.owner == resource_owner,
            )
        ).first()
        if workspace is None:
            raise ValueError(f"no workspace found for object {object_key}")

        primary_key = (
            f"{parent_index.s3_api_url}:{parent_index.s3_bucket}"
            f":{parent_index.s3_root}:{object_key}"
        ).encode("utf-8")
        primary_key_short_sha256 = hashlib.sha256(primary_key).hexdigest()[-16:]
        if record.eventName in [
            "s3:ObjectCreated:Put",
            "s3:ObjectCreated:Post",
            "s3:ObjectCreated:Copy",
        ]:
            # Creaete a new record in elasticsearch
            # this could be an overwrite operation, so query for the old record first.
            doc = event_schemas.IndexDocument(
                time=record.eventTime,
                size=record.s3.object.size,
                eTag=record.s3.object.eTag,
                workspace_id=workspace.id,
                workspace_name=workspace.name,
                owner_id=resource_owner.id,
                owner_name=resource_owner.username,
                bucket=record.s3.bucket.name,
                server=parent_index.s3_api_url,
                root=parent_index.s3_root,
                path=workspace_inner_path,
                user_shares=[share.sharee.id for share in workspace.shares],
                # TODO: group shares
            )
            bulk_operations += (
                json.dumps(
                    {
                        "update": {
                            "_index": parent_index.index_type,
                            "_id": primary_key_short_sha256,
                        }
                    },
                )
                + "\n"
            )
            bulk_operations += event_schemas.UpsertIndexDocument(doc=doc).json() + "\n"

        elif record.eventName in ["s3:ObjectRemoved:Delete"]:
            # Remove an existing record
            bulk_operations += (
                json.dumps(
                    {
                        "delete": {
                            "_index": parent_index.index_type,
                            "_id": primary_key_short_sha256,
                        }
                    }
                )
                + "\n"
            )
        else:
            raise ValueError(
                f"Bucket notification type unsupported: {record.eventName}"
            )
    ec.bulk(bulk_operations)
