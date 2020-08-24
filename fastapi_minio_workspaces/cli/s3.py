import os
import sys
import click

from fastapi_minio_workspaces import schemas, s3utils
from .util import exit_with, handle_request_error

COMMON_ARGS = (
    "aws",
    "--endpoint-url",
    "http://localhost:9000",
    "s3api",
)


def make(cli: click.Group):
    @cli.group(name="s3")
    def s3():
        pass

    @s3.command(name="list")
    @click.argument("workspace_id")
    @click.argument("path", default="")
    @click.pass_obj
    def workspace_list_contents(ctx, workspace_id, path):
        if "public" in workspace_id:
            prefix = workspace_id
            workspace_id = None
        # TODO: cache tokens locally rather than fetching from server
        token_r = ctx["session"].post("token", json={"workspace_id": workspace_id})

        if token_r.ok:
            if workspace_id:
                workspace = schemas.WorkspaceDB.parse_obj(token_r.json()["workspace"])
                prefix = s3utils.getWorkspaceKey(workspace)
            command = (
                *COMMON_ARGS,
                "list-objects-v2",
                "--bucket",
                "fast",
                "--prefix",
                os.path.join(prefix, path),
            )
            os.execvp(command[0], command)
        else:
            exit_with(handle_request_error(token_r))
