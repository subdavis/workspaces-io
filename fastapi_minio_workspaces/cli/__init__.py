import json
import os
from urllib.parse import urlparse
from typing import Optional

import click
import requests
from requests.exceptions import RequestException
from requests_toolbelt.sessions import BaseUrlSession

from . import workspace, auth


class FmiSession(BaseUrlSession):
    def __init__(self, base_url: str, token: Optional[str]):
        base_url = (
            f'{base_url.rstrip("/")}/'  # tolerate input with or without trailing slash
        )
        super(FmiSession, self).__init__(base_url=base_url)
        if token:
            token = token.strip()
        self.token = token
        self.headers.update(
            {
                "User-agent": f"fmi",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.token}",
            }
        )


@click.group()
@click.option(
    "--api-url", default="http://localhost:8000/api", envvar="FMI_ENDPOINT_URL"
)
@click.option("--token", envvar="FMI_TOKEN")
@click.version_option()
@click.pass_context
def cli(ctx, api_url, token):
    session = FmiSession(api_url, token)
    ctx.obj = {"session": session}


cli.add_command(workspace.workspace)
cli.add_command(auth.login)
cli.add_command(auth.register)
