import json
import uuid
from typing import Dict

import jwt
import requests
import uvicorn
from fastapi import Depends
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRouter
from fastapi.security.utils import get_authorization_scheme_param

from workspacesio import database, schemas, settings
from workspacesio.depends import get_db
from workspacesio.utils import build_url

from . import schemas as auth_schemas, depends as auth_depends

router = APIRouter()

REDIRECT_URI = build_url(
    settings.PUBLIC_NAME,
    "/auth",
)
KEYCLOAK_AUTH_URL = build_url(
    settings.KEYCLOAK_PUBLIC_URL,
    f"/auth/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/auth",
    {
        "response_type": "code",
        "client_id": settings.KEYCLOAK_CLIENT_ID,
    },
)
KEYCLOAK_TOKEN_URL = build_url(
    settings.KEYCLOAK_PRIVATE_URL,
    f"/auth/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token",
)


@router.get("/login")
async def login() -> RedirectResponse:
    return RedirectResponse(url=KEYCLOAK_AUTH_URL)


@router.get("/auth")
async def auth(code: str) -> RedirectResponse:
    resp = requests.post(
        KEYCLOAK_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.PUBLIC_NAME,
            "client_id": settings.KEYCLOAK_CLIENT_ID,
        },
    )
    resp.raise_for_status()
    token = auth_schemas.OpenIDTokenResponse(**resp.json())
    print(token)
    jwt.decode(token.access_token, settings.KEYCLOAK_PUBLIC_KEY)
    response = RedirectResponse(url="/")
    response.set_cookie("session", value=token.access_token)
    return response


@router.get("/")
async def root(user: schemas.UserDB = Depends(auth_depends.get_session_user)) -> str:
    return "Hello logged in user"
