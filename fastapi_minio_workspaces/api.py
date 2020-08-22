import boto3
from botocore.client import Config
from fastapi import Depends
from fastapi_users import FastAPIUsers
from fastapi.routing import APIRouter
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import SQLAlchemyUserDatabase

from . import crud, database, models, schemas, settings

router = APIRouter()
user_db = SQLAlchemyUserDatabase(schemas.UserDB, database.database, models.User.__table__)
jwt_authentication = JWTAuthentication(
	secret=settings.SECRET, lifetime_seconds=3600, tokenUrl="/auth/jwt/login"
)
fastapi_users = FastAPIUsers(
	user_db, [jwt_authentication], schemas.UserBase, schemas.UserCreate, schemas.UserUpdate, schemas.UserDB,
)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_boto_s3():
    yield boto3.client(
        's3',
        region_name=settings.AWS_REGION_NAME,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
		config=Config(signature_version='s3v4'),
    )


def get_boto_sts():
	yield boto3.client(
        'sts',
        region_name=settings.AWS_REGION_NAME,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


@router.post('/workspace/', response_model=schemas.WorspaceDB)
def create_workspace(
	workspace: schemas.WorkspaceCreate,
	user: schemas.UserDB = Depends(fastapi_users.get_current_user),
	db: database.SessionLocal = Depends(get_db),
	boto_s3: boto3.Session = Depends(get_boto_s3),
):
	return crud.workspace_create(db, boto_s3, workspace, user)
