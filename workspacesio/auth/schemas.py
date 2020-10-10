from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel


class OpenIDTokenResponse(BaseModel):
    access_token: str
    expires_in: int
    refresh_expires_in: Optional[int]
    refresh_token: Optional[str]
    token_type: str
    session_state: str
    scope: str


class RealmResponse(BaseModel):
    realm: str
    public_key: str
