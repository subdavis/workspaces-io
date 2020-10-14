import json
import uuid
import datetime
import bcrypt
import secrets
from typing import Any, Dict, List, Optional, Tuple, Union

import jwt
import jwt.algorithms
import jwt.exceptions
import requests
import uvicorn
from fastapi import Depends, Header, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRouter
from fastapi.security import APIKeyCookie, OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel

from workspacesio import database, depends, models, schemas
from workspacesio.depends import get_db
from workspacesio.settings import settings
from workspacesio.utils import build_url

## These schemas are separate from the main schemas
## because they should never be used external to this file


class JWToken(BaseModel):
    email: str
    sub: str  # primary key
    iat: int
    exp: int

    given_name: Optional[str]
    picture: Optional[str]

    verified: bool = False


class OIDCJWTokenResponse(BaseModel):
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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
oidc_conf: Union[OIDCConfig, None] = None


def _openid_config():
    global oidc_conf
    if oidc_conf is None:
        wellknown_resp = requests.get(settings.oidc_well_known_url)
        wellknown_resp.raise_for_status()
        wellknown = OIDCWellKnown(**wellknown_resp.json())

        keys_resp = requests.get(wellknown.jwks_uri)
        keys_resp.raise_for_status()
        keys = OIDCKeys(**keys_resp.json())

        public_keys: Dict[str, Any] = {}
        for jwk in keys.keys:
            kid = jwk["kid"]
            public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))

        oidc_conf = OIDCConfig(
            well_known=wellknown,
            keys=public_keys,
        )
    yield oidc_conf


def _verify_jwt(token: str, config: OIDCConfig, verify=True) -> JWToken:
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
    return JWToken(**decoded, verified=verify)


def _verify_token(token, hashed_token):
    pass


def _maybe_session_user(
    session: str = Depends(sessioncookie),
    config: OIDCConfig = Depends(_openid_config),
    db: database.SessionLocal = Depends(depends.get_db),
) -> Optional[JWToken]:
    """
    Load user without verifying session.
    """
    if session is None:
        return None

    try:
        return _verify_jwt(session, config)
    except jwt.exceptions.DecodeError as e:
        return _verify_jwt(session, config, verify=False)


def _make_redirect(config: OIDCConfig, user: Optional[models.User]) -> RedirectResponse:
    # https://auth0.com/docs/api/authentication#dynamic-application-client-registration
    args = {
        "response_type": "code",
        "client_id": settings.oidc_client_id,
        "scope": "openid given_name email picture",
        "redirect_uri": build_url(settings.public_name, "/auth"),
    }
    if user is not None:
        # attempt a silent auth
        args["prompt"] = "none"
    return RedirectResponse(
        url=build_url(config.well_known.authorization_endpoint, args_dict=args)
    )


def get_current_user(
    session_cookie: Optional[JWToken] = Depends(_maybe_session_user),
    token: str = Depends(oauth2_scheme),
    db: database.SessionLocal = Depends(depends.get_db),
) -> models.User:

    if session_cookie is not None and session_cookie.verified:
        user = (
            db.query(models.User).filter(models.User.sub == session_cookie.sub).first()
        )
        if user is not None:
            return user
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")


@router.get("/login")
async def login(
    config: OIDCConfig = Depends(_openid_config),
    pair: Tuple[Optional[JWToken], Optional[models.User]] = Depends(
        _maybe_session_user
    ),
) -> RedirectResponse:
    return _make_redirect(config, pair[1])


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/app")
    response.set_cookie("session", value="", samesite="lax", httponly=True, expires=0)
    return response


@router.get("/auth")
async def auth(
    code: Optional[str] = None,
    error: Optional[str] = None,
    config: OIDCConfig = Depends(_openid_config),
    db: database.SessionLocal = Depends(depends.get_db),
) -> RedirectResponse:
    if error is not None:
        return _make_redirect(config, None)
    if code is None:
        raise HTTPException(400, "No error, code missing.")
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
    token = OIDCJWTokenResponse(**resp.json())
    verified = _verify_jwt(token.id_token, config)

    user: schemas.UserDB = (
        db.query(models.User).filter(models.User.email == verified.email).first()
    )

    if user is None:
        user = models.User(
            username=verified.nickname or verified.email,
            email=verified.email,
        )
        db.add(user)
        db.commit()

    response = RedirectResponse(url="/app")
    response.set_cookie("session", value=token.id_token, samesite="lax", httponly=True)
    return response


@router.get("/")
def root(session: str = Depends(sessioncookie)) -> RedirectResponse:
    return session
