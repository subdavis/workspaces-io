from typing import List, Optional

from fastapi.routing import APIRouter
from fastapi_users import FastAPIUsers

from workspacesio import database, schemas
from workspacesio.depends import fastapi_users, get_db

from . import crud
from . import models as deriv_models
from . import schemas as deriv_schemas

router = APIRouter()
tags = ["derivatives"]


@router.post(
    "/derivative",
    response_model=deriv_schemas.DerivativeDB,
    status_code=201,
)
def create_derivative(
    params: deriv_schemas.DerviativeCreate,
    creator: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.deriv_create(db, creator, params)


@router.get("/derivative", response_model=List[deriv_schemas.DerivativeDB])
def find_derivatives(
    prefix: str,
    name: Optional[str],
    user: schemas.UserBase = Depends(fastapi_users.get_current_user),
    db: database.SessionLocal = Depends(get_db),
):
    return crud.deriv_search(db, user, name, prefix)
