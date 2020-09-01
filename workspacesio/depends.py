"""
FastAPI endpoint dependencies
"""
import hashlib
from typing import Union

import boto3
from botocore.client import Config
from elasticsearch import Elasticsearch
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import SQLAlchemyUserDatabase

from . import database, dbutils, models, schemas, settings

user_db = SQLAlchemyUserDatabase(
    schemas.UserDB, database.database, models.User.__table__
)
jwt_authentication = JWTAuthentication(
    secret=settings.SECRET, lifetime_seconds=3600, tokenUrl="/auth/jwt/login"
)
fastapi_users = FastAPIUsers(
    user_db,
    [jwt_authentication],
    schemas.UserBase,
    schemas.UserCreate,
    schemas.UserUpdate,
    schemas.UserDB,
)


class Boto3ClientCache:
    """
    There may be many s3 nodes in the cluser.  Once a client has been established,
    cache it for future use.  This class works for sts and s3 type clients.
    """

    def __init__(self):
        self.cache: Dict[str, boto3.Session] = {}

    def get_client(
        self, client_type: str, node: Union[models.StorageNode, schemas.StorageNodeDB]
    ) -> boto3.Session:
        primary_key = (
            (
                f"{client_type}{node.region_name}{node.api_url}"
                f"{node.access_key_id}{node.secret_access_key}"
            )
            .lower()
            .encode("utf-8")
        )
        primary_key_short_sha256 = hashlib.sha256(primary_key).hexdigest()
        client = self.cache.get(primary_key_short_sha256, None)
        if client is None:
            config = Config()
            if client_type == "s3":
                config = Config(signature_version="s3v4")
            client = boto3.client(
                client_type,
                region_name=node.region_name,
                endpoint_url=node.api_url,
                aws_access_key_id=node.access_key_id,
                aws_secret_access_key=node.secret_access_key,
                config=config,
            )
            self.cache[primary_key_short_sha256] = client
        return client


def get_db():
    db = database.SessionLocal(query_cls=dbutils.Query)
    try:
        yield db
    finally:
        db.close()


def get_boto():
    yield Boto3ClientCache()


def get_elastic_client():
    client = Elasticsearch(settings.ES_NODES)
    try:
        yield client
    finally:
        client.close()
