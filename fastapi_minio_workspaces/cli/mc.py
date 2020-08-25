import os
import sys
import re
from typing import Tuple, List

import click

from fastapi_minio_workspaces import schemas, s3utils
from .util import exit_with, handle_request_error


COMMON_ARGS = (
    "mc",
    "--endpoint-url",
    "http://localhost:9000",
    "s3api",
)

special = re.compile(
    "\/?(?P<scope>(public)|(private))(\/(?P<user>[^\/]*)(\/((?P<ws>[^\/]*))(\/(?P<path>.*))?)?)?"
)


def find_dependencies(args: List[str]):
    required_workspaces = []
    for arg in args:
        m = special.match(arg)
        if m is not None:
            groups = m.groups()
            required_workspaces.append(
                {
                    "scope": groups[0],
                    "user": groups[4],
                    "workspace": groups[6],
                    "path": groups[9],
                    "arg": arg,
                }
            )
    return required_workspaces


def make(cli: click.Group):
    @cli.command(name="mc", context_settings=dict(ignore_unknown_options=True,))
    @click.argument("args", nargs=-1)
    @click.pass_obj
    def mc(ctx, args):
        dependents = find_dependencies(args)
        if len(dependents) > 1:
            click.echo("Greater than 1 workspace not supported")

        body = []
        for d in dependents:
            workspace_name = d["workspace"]
            owner_name = d["user"]
            body.append(
                {"workspace_name": workspace_name, "owner_name": owner_name,}
            )
        r = ctx["session"].post("token/search", json=body)
        if r.ok:
            data = r.json()
            workspaces = data["workspaces"]
            access_key = data["token"]["access_key_id"]
            secret = data["token"]["secret_access_key"]
            session_token = data["token"]["session_token"]
            mc_env = f"http://{access_key}:{secret}:{session_token}@localhost:9000"

            assembled = " ".join(args)

            if len(workspaces):
                for d in dependents:
                    path = os.path.join(
                        f"myalias/{workspaces[0]['bucket']}", d["arg"].lstrip(os.sep)
                    )
                    assembled = assembled.replace(d["arg"], path)
            command = (
                "mc",
                *assembled.split(" "),
            )
            os.execvpe(command[0], command, dict(os.environ, MC_HOST_myalias=mc_env))
        else:
            exit_with(handle_request_error(r))
