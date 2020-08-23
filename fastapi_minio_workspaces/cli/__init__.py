import json
import os
from typing import Optional
from urllib.parse import urlparse

import click
import requests
from click_aliases import ClickAliasedGroup
from requests.exceptions import RequestException
from requests_toolbelt.sessions import BaseUrlSession

from . import auth, s3token, workspace, s3


class FmmSession(BaseUrlSession):
    def __init__(self, base_url: str, token: Optional[str]):
        base_url = (
            f'{base_url.rstrip("/")}/'  # tolerate input with or without trailing slash
        )
        super(FmmSession, self).__init__(base_url=base_url)
        if token:
            token = token.strip()
        self.token = token
        self.headers.update(
            {
                "User-agent": f"fmm",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.token}",
            }
        )


@click.group(cls=ClickAliasedGroup)
@click.option(
    "--api-url", default="http://localhost:8000/api", envvar="FMM_ENDPOINT_URL"
)
@click.option("--token", envvar="FMM_TOKEN")
@click.version_option()
@click.pass_context
def cli(ctx, api_url, token):
    session = FmmSession(api_url, token)
    ctx.obj = {"session": session}


workspace.make(cli)
auth.make(cli)
s3token.make(cli)
s3.make(cli)
