"""
FastAPI endpoint dependencies
"""
import boto3
from botocore.client import Config
from elasticsearch import Elasticsearch
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication

from . import database, dbutils, settings, models, schemas

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


def get_db():
    db = database.SessionLocal(query_cls=dbutils.Query)
    try:
        yield db
    finally:
        db.close()


def get_boto_s3():
    yield boto3.client(
        "s3",
        region_name=settings.AWS_REGION_NAME,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )


def get_boto_sts():
    yield boto3.client(
        "sts",
        region_name=settings.AWS_REGION_NAME,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def get_elastic_client():
    client = Elasticsearch(settings.ES_NODES)
    try:
        yield client
    finally:
        client.close()
