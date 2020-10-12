import json
from typing import Dict, List, Optional

import click
from pydantic import BaseModel

from workspacesio import schemas


class Config(BaseModel):
    token: Optional[str]
    api_url: Optional[str]


def make() -> Config:
    return Config()


def save_config(c: Config, p: str):
    with open(p, "w") as out:
        out.write(c.json())


def load_config(c: str) -> Config:
    try:
        return Config(**json.loads(c))
    except:
        return make()


def resolve_token(c: Config, query: str) -> Optional[schemas.S3TokenDB]:
    """
    validate a workspace string, see if I have it locally
    """
    pass
