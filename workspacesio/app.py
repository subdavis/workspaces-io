import os
import typing

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.logger import logger
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import api, auth, crud, database, depends, indexing, models, schemas, settings


def create_app(env: typing.Dict[str, str]) -> FastAPI:
    app = FastAPI(
        title="WorkspacesIO",
        version="0.1.0",
    )
    app.include_router(api.router, prefix="/api")
    app.include_router(indexing.api.router, prefix="/api")
    app.include_router(auth.router)
    if os.path.exists("./static"):
        app.mount("/app", StaticFiles(directory="static", html=True), name="static")
    else:
        logger.error("ERROR:\tStatic directory not found.")

    crud.register_handlers(app)
    return app
