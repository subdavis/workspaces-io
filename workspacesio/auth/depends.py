from typing import Optional

from fastapi import Depends, Header, HTTPException, Cookie
from fastapi.security import APIKeyCookie
import jwt

from workspacesio import settings, depends, database

sessioncookie = APIKeyCookie(name="session")


async def get_session_user(
    session: str = Depends(sessioncookie),
    db: database.SessionLocal = Depends(depends.get_db),
):
    """
    Session user is authenticated statelessly through an OpenID id_token
    https://github.com/tiangolo/fastapi/issues/754
    """
    try:
        print(session)
        payload = jwt.decode(session, settings.KEYCLOAK_PUBLIC_KEY)
        print(payload)
    except Exception as e:
        raise HTTPException(401, str(e))


async def get_current_user(
    x_workspaces_token: Optional[str] = Header(None),
    db: database.SessionLocal = Depends(depends.get_db),
):
    return None
