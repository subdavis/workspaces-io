import os
import re
import sys
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
    @cli.command(name="mc", context_settings=dict(ignore_unknown_options=True,))
    @click.argument("args", nargs=-1)
    @click.pass_obj
    def mc(ctx, args):
        r = ctx["session"].post(
            "token/search", json={"search_terms": args, "sep": os.sep,}
        )
        if r.ok:
            response = r.json()
            assembled = " ".join(args)
            for arg, workspace in response["workspaces"].items():
                path = os.path.join(
                    f"myalias/{workspace['bucket']}", arg.lstrip(os.sep)
                )
                assembled = assembled.replace(arg, path)
            access_key = response["token"]["access_key_id"]
            secret = response["token"]["secret_access_key"]
            session_token = response["token"]["session_token"]
            mc_env = f"http://{access_key}:{secret}:{session_token}@localhost:9000"
            command = (
                "mc",
                *assembled.split(" "),
            )
            os.execvpe(command[0], command, dict(os.environ, MC_HOST_myalias=mc_env))
        else:
            exit_with(handle_request_error(r))
