from typing import List, Optional

from fastapi import Depends
from fastapi.routing import APIRouter

from workspacesio import auth, database, schemas
from workspacesio.depends import get_db

from . import crud
from . import models as artifact_models
from . import schemas as artifact_schemas

router = APIRouter()
tags = ["artifacts"]


@router.post(
    "/artifact",
    response_model=artifact_schemas.ArtifactDB,
    status_code=201,
)
def create_artifact(
    params: artifact_schemas.DerviativeCreate,
    creator: schemas.UserDB = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.artifact_create(db, creator, params)


@router.get("/artifact", response_model=List[artifact_schemas.ArtifactDB])
def find_artifacts(
    prefix: str,
    name: Optional[str],
    user: schemas.UserDB = Depends(auth.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.artifact_search(db, user, name, prefix)
