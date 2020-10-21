import json
import os
from typing import Optional
from urllib.parse import urlparse

import click
import requests
import requests.auth
from click_aliases import ClickAliasedGroup
from requests.exceptions import RequestException
from requests_toolbelt.sessions import BaseUrlSession

from . import auth, config, index, mc, node, root, s3token, search, user, workspace


class WioSession(BaseUrlSession):
    def __init__(self, cfg: config.Config):
        base_url = cfg.api_url
        base_url = (
            f'{base_url.rstrip("/")}/'  # tolerate input with or without trailing slash
        )
        super(WioSession, self).__init__(base_url=base_url)
        auth = None
        if cfg.access_key and cfg.secret_key:
            auth = (cfg.access_key, cfg.secret_key)
            self.headers.update(
                {
                    "Authorization": requests.auth._basic_auth_str(
                        cfg.access_key, cfg.secret_key
                    ),
                }
            )
        self.headers.update(
            {
                "User-agent": f"wio",
                "Accept": "application/json",
            }
        )


@click.group(cls=ClickAliasedGroup)
@click.option("--api-url", envvar="WIO_ENDPOINT_URL")
@click.option(
    "--config-path",
    default=os.path.join(os.path.expanduser("~"), ".config", "wio.json"),
    envvar="WIO_CONFIG_PATH",
    type=click.Path(dir_okay=False, file_okay=True, writable=True, resolve_path=True),
)
@click.version_option()
@click.pass_context
def cli(ctx, api_url, config_path):
    conf = config.load_config(config_path)
    if api_url:
        conf.api_url = api_url
    ctx.obj = {
        "configPath": config_path,
        "config": conf,
        "session": WioSession(conf),
    }


workspace.make(cli)
auth.make(cli)
s3token.make(cli)
mc.make(cli)
index.make(cli)
node.make(cli)
root.make(cli)
search.make(cli)
user.make(cli)
