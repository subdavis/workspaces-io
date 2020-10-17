"""
FastAPI endpoint dependencies
"""
from elasticsearch import Elasticsearch

from workspacesio.common import s3utils

from . import database, dbutils, settings


def get_db():
    db = database.SessionLocal(query_cls=dbutils.Query)
    try:
        yield db
    finally:
        db.close()


def get_boto():
    yield s3utils.Boto3ClientCache()


def get_elastic_client():
    client = Elasticsearch(settings.settings.es_nodes)
    try:
        yield client
    finally:
        client.close()
