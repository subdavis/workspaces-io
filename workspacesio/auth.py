import json
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

import jwt
import jwt.algorithms
import jwt.exceptions
import requests
import uvicorn
from fastapi import Depends, Header, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRouter
from fastapi.security import APIKeyCookie
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel

from workspacesio import database, depends, models, schemas
from workspacesio.depends import get_db
from workspacesio.settings import settings
from workspacesio.utils import build_url

## These schemas are separate from the main schemas
## because they should never be used external to this file


class Token(BaseModel):
    nickname: str
    email: str
    iat: int
    exp: int

    given_name: Optional[str]
    picture: Optional[str]

    verified: bool = False


class OIDCTokenResponse(BaseModel):
    id_token: str
    access_token: str
    expires_in: int
    refresh_expires_in: Optional[int]
    refresh_token: Optional[str]
    token_type: str
    scope: str


class OIDCWellKnown(BaseModel):
    issuer: str
    token_endpoint: str
    authorization_endpoint: str
    jwks_uri: str


class OIDCKeys(BaseModel):
    keys: List[Dict[str, Union[str, List[str]]]]


class OIDCConfig(BaseModel):
    well_known: OIDCWellKnown
    keys: Dict[str, Any]


router = APIRouter()

sessioncookie = APIKeyCookie(name="session", auto_error=False)
oidc_conf: Union[OIDCConfig, None] = None


def openid_config():
    global oidc_conf
    if oidc_conf is None:
        wellknown_resp = requests.get(settings.oidc_well_known_url)
        wellknown_resp.raise_for_status()
        wellknown = OIDCWellKnown(**wellknown_resp.json())

        keys_resp = requests.get(wellknown.jwks_uri)
        keys_resp.raise_for_status()
        keys = OIDCKeys(**keys_resp.json())

        print(keys.to_string())
        print(wellknown.to_string())
        public_keys: Dict[str, Any] = {}
        for jwk in keys.keys:
            kid = jwk["kid"]
            public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))

        oidc_conf = OIDCConfig(
            well_known=wellknown,
            keys=public_keys,
        )
    yield oidc_conf


def verify_token(token: str, config: OIDCConfig, verify=True) -> Token:
    kid = jwt.get_unverified_header(token)["kid"]
    key = config.keys.get(kid)
    if key is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "key ID not found in openid config"
        )

    # Audience is tricky
    # https://github.com/jpadilla/pyjwt/issues/198
    # https://auth0.com/docs/tokens/access-tokens/get-access-tokens
    decoded = jwt.decode(
        token,
        key,
        algorithms=settings.oidc_algos,
        audience=settings.oidc_client_id,
        verify=verify,
    )
    return Token(**decoded, verified=verify)


def get_session_user(
    session: str = Depends(sessioncookie),
    config: OIDCConfig = Depends(openid_config),
    db: database.SessionLocal = Depends(depends.get_db),
) -> models.User:
    """
    Session user is authenticated statelessly through an OpenID id_token
    https://github.com/tiangolo/fastapi/issues/754
    """
    if session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")
    token = verify_token(session, config)
    return db.query(models.User).filter(models.User.email == token.email).first_or_404()


def maybe_session_user(
    session: str = Depends(sessioncookie),
    config: OIDCConfig = Depends(openid_config),
    db: database.SessionLocal = Depends(depends.get_db),
) -> Tuple[Optional[Token], Optional[models.User]]:
    """
    Load user without verifying session.
    """
    if session is None:
        return (None, None)

    try:
        token = verify_token(session, config)
    except jwt.exceptions.DecodeError as e:
        token = verify_token(session, config, verify=False)

    return (
        token,
        db.query(models.User).filter(models.User.email == token.email).first(),
    )


def get_current_user(
    x_workspaces_token: Optional[str] = Header(None),
    db: database.SessionLocal = Depends(depends.get_db),
):
    return None


def make_redirect(config: OIDCConfig, user: Optional[models.User]) -> RedirectResponse:
    # https://auth0.com/docs/api/authentication#dynamic-application-client-registration
    args = {
        "response_type": "code",
        "client_id": settings.oidc_client_id,
        "redirect_uri": build_url(settings.public_name, "/auth"),
    }
    if user is not None:
        # attempt a silent auth
        args["prompt"] = "none"
    return RedirectResponse(
        url=build_url(config.well_known.authorization_endpoint, args_dict=args)
    )


@router.get("/login")
async def login(
    config: OIDCConfig = Depends(openid_config),
    pair: Tuple[Optional[Token], Optional[models.User]] = Depends(maybe_session_user),
) -> RedirectResponse:
    return make_redirect(config, pair[1])


@router.get("/auth")
async def auth(
    code: str,
    error: Optional[str],
    config: OIDCConfig = Depends(openid_config),
    db: database.SessionLocal = Depends(depends.get_db),
) -> RedirectResponse:
    if error is not None:
        return make_redirect(config, None)
    # https://auth0.com/docs/api/authentication#get-token
    resp = requests.post(
        config.well_known.token_endpoint,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": build_url(settings.public_name, "/auth"),
            "client_id": settings.oidc_client_id,
            "client_secret": settings.oidc_client_secret,
        },
    )
    resp.raise_for_status()
    token = OIDCTokenResponse(**resp.json())
    verified = verify_token(token.id_token, config)

    user: schemas.UserDB = (
        db.query(models.User).filter(username=verified.nickname).first()
    )
    if user is None:
        # TODO: make new user
        pass

    response = RedirectResponse(url="/")
    response.set_cookie("session", value=token.id_token)
    return response


@router.get("/")
async def root(user: schemas.UserDB = Depends(get_session_user)) -> str:
    return "Hello logged in user"
