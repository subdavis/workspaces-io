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


def group_workspaces_by_node(
    workspaces: List[models.Workspace],
) -> Dict[uuid.UUID, List[models.Workspace]]:
    """Group workspaces by their node ID"""
    # group the workspace query list by server because a distinct S3 token
    # is needed for each member of that group.
    node_groups: Dict[uuid.UUID, List[models.Workspace]] = {}
    for w in workspaces:
        node_id = w.root.storage_node.id
        if node_id in node_groups:
            node_groups[node_id].append(w)
        else:
            node_groups[node_id] = [w]
    return node_groups


def segment_workspaces(
    db: Session, workspaces: List[models.Workspace], requester: schemas.UserDB
) -> Tuple[
    List[models.Workspace],
    List[Tuple[models.Workspace, models.Share]],
    List[models.WorkspaceRoot],
]:
    # foreign workspaces are the matches that have an owner other than the requester
    # that the requester DOES have a share for.  If the workspace is public and unshared,
    # Access is covered by the default policy
    requester_workspaces: List[models.Workspace] = []
    foreign_workspaces: List[Tuple[models.Workspace, models.Share]] = []
    for w in workspaces:
        if w.owner_id != requester.id:
            share: models.Share = db.query(models.Share).filter(
                and_(
                    models.Share.workspace_id == w.id,
                    models.Share.sharee_id == requester.id,
                )
            ).first()
            if share:
                foreign_workspaces.append((w, share,))
            elif w.root.root_type == schemas.RootType.PUBLIC:
                # it's not the requester's workspace, but it's public-readable
                requester_workspaces.append(w)
            else:
                # assume the matching workspace is a coincidence, and the user
                # actually meant to reference a path on their own disk.
                # This is a permissions error, but failing silently will give
                raise PermissionError(
                    f"User {requester.username} is not permitted to access {w.name}"
                )
        else:
            requester_workspaces.append(w)
    seen_roots = set()
    return (
        requester_workspaces,
        foreign_workspaces,
        # https://stackoverflow.com/questions/10024646/how-to-get-list-of-objects-with-unique-attribute
        [
            seen_roots.add(w.root_id) or w.root
            for w in requester_workspaces
            if w.root_id not in seen_roots
        ],
    )


def get_token_for_workspace_constellation(
    db: Session,
    requester_id: uuid.UUID,
    workspaces: List[models.Workspace],
    foreign_workspaces=List[models.Workspace],
) -> Optional[models.S3Token]:
    """
    Workspace constellation must all be from the same server
    """
    raw_query = """
    SELECT token.id as token_id
    FROM minio_token mt
    LEFT JOIN workspace_s3token_association_table wsa
        ON wsa.s3token_id = mt.id
    JOIN workspace w
        ON w.id = wsa.workspace_id
        AND w.owner_id = ANY(:foreign_ids)
    LEFT JOIN root_s3token_association_table rsa
        ON rsa.s3token_id = mt.id
    JOIN workspace_root wr
        ON wr.id = rsa.root_id
    ...
    """
    query = db.query(models.S3Token)
    filters = []
    if len(foreign_workspaces) > 0:
        query = query.outerjoin(models.Workspace, models.S3Token.workspaces)
        filters.append(or_(*[models.Workspace.id == w.id for w in foreign_workspaces]))
    if len(workspaces) > 0:
        query = query.outerjoin(models.WorkspaceRoot, models.S3Token.roots)
        filters.append(
            or_(*[models.WorkspaceRoot.id == w.root_id for w in workspaces]),
        )

    # https://stackoverflow.com/questions/11468572/postgresql-where-all-in-array
    query = (
        query.filter(and_(models.S3Token.owner_id == requester_id, *filters))
        .group_by(models.S3Token.id)
        .having(func.count("*") >= (len(foreign_workspaces) + len(workspaces)))
    )
    return query.first()


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
        .first()
    )
    if node is None:
        raise ValueError(f"No root with name {params.node_name}")
    root_db = models.WorkspaceRoot(
        root_type=params.root_type,
        base_path=params.base_path.strip("/"),
        bucket=params.bucket.strip("/"),
        node_id=node.id,
    )
    db.add(root_db)
    db.flush()
    b3.create_bucket(ACL="private", Bucket=root_db.bucket)
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
    """Create a workspace for owner, including an empty root object in s3"""
    db_owner: models.User = db.query(models.User).get_or_404(owner.id)
    # TODO: heuristic to decide which root to put a workspace in
    root_type: schemas.RootType = (
        schemas.RootType.PUBLIC if workspace.public else schemas.RootType.PRIVATE
    )
    # find roots that are compatible with the workspace's management style
    db_root_q = db.query(models.WorkspaceRoot).filter(
        models.WorkspaceRoot.root_type == root_type
    )
    # if the user has asked to be placed in a particular node
    if workspace.node_name:
        db_root_q = db_root_q.filter(
            models.WorkspaceRoot.storage_node.has(name=workspace.node_name)
        )
    db_root: models.WorkspaceRoot = db_root_q.first()
    if db_root is None:
        raise ValueError(f"No available roots found.  Contact your administrator")
    db_workspace = models.Workspace(
        name=workspace.name, owner_id=owner.id, root_id=db_root.id
    )
    db.add(db_workspace)
    db.flush()
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
) -> List[models.S3Token]:
    """Create s3 sts token for requester if they have permissions"""
    # Find all workspaces in the query
    workspace_query_list: List[models.Workspace] = db.query(models.Workspace,).filter(
        models.Workspace.id.in_(token.workspaces)
    ).all()

    if len(workspace_query_list) == 0:
        return []

    tokens: List[models.S3Token] = []
    groups = group_workspaces_by_node(workspace_query_list)

    for node_id, workspaces in groups.items():
        my_workspaces, foreign_workspaces, roots = segment_workspaces(
            db=db, workspaces=workspaces, requester=requester
        )
        existing = get_token_for_workspace_constellation(
            db=db,
            requester_id=requester.id,
            workspaces=my_workspaces,
            foreign_workspaces=[f[0] for f in foreign_workspaces],
        )
        if existing and existing.expiration > datetime.datetime.utcnow():
            tokens.append(existing)
            continue
        else:
            policy = s3utils.makePolicy(
                requester,
                workspaces=my_workspaces,
                foreign_workspaces=foreign_workspaces,
            )
            token_args = dict(
                owner_id=requester.id,
                policy=policy,
                workspaces=foreign_workspaces,
                roots=roots,
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
            tokens.append(token_db)
    return tokens


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
    tokens: List[models.S3Token] = []
    for path in search.search_terms:
        match, interior_path = match_terms(db, requester, path)
        if match:
            workspaces[path] = schemas.S3TokenSearchResponseWorkspacePart(
                workspace=match, path=interior_path,
            )
    workspace_id_list = [w.workspace.id for w in workspaces.values()]
    unique_workspace_id_list = list(set(workspace_id_list))
    if len(workspace_id_list):
        tokens = token_create(
            db,
            b3,
            requester,
            schemas.S3TokenCreate(workspaces=unique_workspace_id_list),
        )
    return schemas.S3TokenSearchResponse(tokens=tokens, workspaces=workspaces,)


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
