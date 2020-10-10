import os
import typing

from fastapi import Depends, FastAPI, Request
from sqlalchemy.orm import Session

from . import api, auth, crud, database, depends, indexing, models, schemas, settings


def create_app(env: typing.Dict[str, str]) -> FastAPI:
    app = FastAPI(
        title="WorkspacesIO",
        version="0.1.0",
    )
    app.include_router(api.router, prefix="/api")
    app.include_router(indexing.api.router, prefix="/api")
    app.include_router(auth.views.router)
    crud.register_handlers(app)
    return app
