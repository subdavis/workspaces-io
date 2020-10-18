from typing import List

from fastapi import Depends
from fastapi.routing import APIRouter

from workspacesio import auth, database, schemas
from workspacesio.depends import get_db

from . import crud
from . import models as annotation_models
from . import schemas as annotation_schemas

router = APIRouter()
tags = ["annotation"]


@router.post(
    "/",
    tags=tags,
    status_code=201,
    response_model=annotation_schemas.AnnotationDatasetDB,
)
def create_annotation_dataset(
    args: annotation_schemas.AnnotationDatasetCreate,
    user: schemas.UserDB = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.annotation_dataset_create(db, user, args)


@router.get(
    "/",
    tags=tags,
    response_model=List[annotation_schemas.AnnotationDatasetDB],
)
def list_annotation_datasets(
    user: schemas.UserDB = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.annotation_dataset_list(db, user)
