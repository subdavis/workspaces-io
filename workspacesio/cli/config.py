import json
import os
from typing import Any, Dict, List, Optional, cast

import click
from pydantic import BaseModel
from requests_toolbelt.sessions import BaseUrlSession

from workspacesio.common import schemas


class Config(BaseModel):
    access_key: Optional[str]
    secret_key: Optional[str]
    api_url: str = "http://localhost:8100/api"


class Ctx(BaseModel):
    config: Config
    configPath: str
    session: BaseUrlSession

    class Config:
        arbitrary_types_allowed = True


def make() -> Config:
    return Config()


def getctx(ctx: Dict[str, Any]) -> Ctx:
    return Ctx(**ctx)


def save(ctx: Ctx):
    with open(ctx.configPath, "w") as out:
        out.write(ctx.config.json())


def load_config(path: str) -> Config:
    if os.path.exists(path):
        try:
            with open(path) as config_file:
                return Config(**json.loads(config_file.read()))
        except:
            return make()
    return make()
