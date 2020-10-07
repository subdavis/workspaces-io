from typing import List, Optional

from fastapi.routing import APIRouter
from fastapi_users import FastAPIUsers

from workspacesio import database, schemas
from workspacesio.depends import fastapi_users, get_db

from . import crud
from . import models as artifact_models
from . import schemas as artifact_schemas

router = APIRouter()
tags = ["artifacts"]


@router.post(
    "/artifact",
    response_model=artifact_schemas.DerivativeDB,
    status_code=201,
)
def create_artifact(
    params: artifact_schemas.DerviativeCreate,
    creator: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.artifact_create(db, creator, params)


@router.get("/artifact", response_model=List[artifact_schemas.DerivativeDB])
def find_artifacts(
    prefix: str,
    name: Optional[str],
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.artifact_search(db, user, name, prefix)


@router.get('/artifact/batch_find', response_model=List[])