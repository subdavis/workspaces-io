import os
import typing

from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session

from . import __version__, api, crud, database, models, schemas, settings


def init_fastapi_users(app: FastAPI):
    def on_after_register(user: schemas.UserDB, request: Request, db: Session = Depends(api.get_db)):
       crud.on_after_register(db, user)

    def on_after_forgot_password(user: schemas.UserDB, token: str, request: Request, db: Session = Depends(api.get_db)):
        crud.on_after_forgot_password(db, user)

    @app.on_event("startup")
    async def startup():
        await database.database.connect()

    @app.on_event("shutdown")
    async def shutdown():
        await database.database.disconnect()

    
    app.include_router(
        api.fastapi_users.get_auth_router(api.jwt_authentication), prefix="/auth/jwt", tags=["auth"]
    )
    app.include_router(
        api.fastapi_users.get_register_router(on_after_register), prefix="/auth", tags=["auth"]
    )
    app.include_router(
        api.fastapi_users.get_reset_password_router(
            settings.SECRET, after_forgot_password=on_after_forgot_password
        ),
        prefix="/auth",
        tags=["auth"],
    )
    app.include_router(api.fastapi_users.get_users_router(), prefix="/users", tags=["users"])


def create_app(env: typing.Mapping[str, str]) -> FastAPI:
    app = FastAPI(title="FastAPI MinIO Workspaces", version=__version__,)
    app.include_router(api.router, prefix="/api")
    init_fastapi_users(app)
    crud.register_handlers(app)
    return app