import os
import re
import sys
import urllib.parse
from typing import Dict, List, Tuple

import click

from workspacesio import s3utils, schemas

from .util import exit_with, handle_request_error

SUPPORTED_MINIO_COMMANDS = [
    "ls",
    "cp",
    "mirror",
    "cat",
    "head",
    "pipe",
    "share",
    "find",
    "sql",
    "stat",
    "mv",
    "tree",
    "du",
    "diff",
    "rm",
    "watch",
]


def isrealpath(s: str) -> bool:
    return os.path.exists(os.path.abspath(os.path.expanduser(s)))


def transform_arguments(args: List[str]):
    """attempt to """
    if len(args) < 2 or not (args[0] in SUPPORTED_MINIO_COMMANDS):
        return []
    possible_workspaces = []
    for arg in args[1:]:
        if arg.startswith("-"):
            continue
        if isrealpath(arg):
            continue
        possible_workspaces.append(arg)
    return possible_workspaces


def make(cli: click.Group):
    @cli.command(
        name="mc",
        context_settings=dict(
            ignore_unknown_options=True,
        ),
    )
    @click.argument("args", nargs=-1)
    @click.pass_obj
    def mc(ctx, args):
        r = ctx["session"].post(
            "token/search",
            json={
                "search_terms": args,
            },
        )
        if r.ok:
            response = r.json()
            assembled = " ".join(args)
            mc_env = ""
            for arg, match in response["workspaces"].items():
                workspace = schemas.WorkspaceDB(**match["workspace"])
                scope = workspace.root.root_type.lower()
                key = s3utils.getWorkspaceKey(workspace)
                path = "/".join(
                    [
                        "myalias",
                        workspace.root.bucket,
                        key,
                        match["path"].lstrip("/"),
                    ]
                )
                assembled = assembled.replace(arg, path)
            if len(response["tokens"]) == 1:
                token = response["tokens"][0]["token"]
                access_key = token["access_key_id"]
                secret = token["secret_access_key"]
                session_token = token["session_token"]
                api_url = response["tokens"][0]["node"]["api_url"]
                url = urllib.parse.urlparse(api_url)
                mc_env = (
                    f"{url.scheme}://{access_key}:{secret}:{session_token}@{url.netloc}"
                )
            command = (
                "mc",
                *assembled.split(" "),
            )
            os.execvpe(command[0], command, dict(os.environ, MC_HOST_myalias=mc_env))
        else:
            exit_with(handle_request_error(r))
