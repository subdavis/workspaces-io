import json
import os
from typing import Optional
from urllib.parse import urlparse

import click
import requests
from click_aliases import ClickAliasedGroup
from requests.exceptions import RequestException
from requests_toolbelt.sessions import BaseUrlSession

from . import index, mc, node, root, s3token, workspace, auth
from . import config as conf

DEFAULT_ENDPOINT = "http://localhost:8100/api"


class WioSession(BaseUrlSession):
    def __init__(
        self,
        base_url: str,
        token: Optional[str] = "",
    ):
        base_url = (
            f'{base_url.rstrip("/")}/'  # tolerate input with or without trailing slash
        )
        super(WioSession, self).__init__(base_url=base_url)
        if token:
            token = token.strip()
        self.token = token
        self.headers.update(
            {
                "User-agent": f"wio",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.token}",
            }
        )


@click.group(cls=ClickAliasedGroup)
@click.option("--api-url", envvar="WIO_ENDPOINT_URL")
@click.option(
    "--config",
    default=os.path.join(os.path.expanduser("~"), ".config", "wio.json"),
    envvar="WIO_CONFIG_PATH",
    type=click.Path(dir_okay=False, file_okay=True, writable=True, resolve_path=True),
)
@click.option("--token", envvar="WIO_TOKEN")
@click.version_option()
@click.pass_context
def cli(ctx, api_url, config, token):
    context = {
        "configPath": config,
    }
    if os.path.exists(config):
        with open(config) as config_file:
            context["config"] = conf.load_config(config_file.read())
    else:
        context["config"] = conf.make()
    if not token:
        token = context["config"].token
    if not api_url:
        api_url = context["config"].api_url
    if not api_url:
        api_url = DEFAULT_ENDPOINT
    context["session"] = WioSession(api_url, token=token)
    ctx.obj = context


workspace.make(cli)
auth.make(cli)
s3token.make(cli)
mc.make(cli)
index.make(cli)
node.make(cli)
root.make(cli)
