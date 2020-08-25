import click
from click_aliases import ClickAliasedGroup

from fastapi_minio_workspaces import schemas

from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @cli.group(name="workspace", cls=ClickAliasedGroup, aliases=["w"])
    def workspace():
        pass

    @workspace.command(name="list", aliases=["ls", "l"])
    @click.option("--name", type=click.STRING, required=False)
    @click.pass_obj
    def list_workspaces(ctx, name):
        params = {}
        if name:
            params["name"] = name
        r = ctx["session"].get("workspace", params=params)
        if r.ok:
            for ws in r.json():
                root = "public" if ws["public"] else "private"
                click.secho(f"[{ws['created']}] ", fg="green", nl=False)
                click.secho(f"{ws['id']} ", fg="yellow", nl=False)
                click.secho(
                    f"{root}/{ws['owner']['username']}/{ws['name']}/",
                    fg="cyan",
                    bold=True,
                )
        else:
            exit_with(handle_request_error(r))

    @workspace.command(name="create", aliases=["c"])
    @click.argument("name")
    @click.option("--public/--private", default=False, is_flag=True)
    @click.pass_obj
    def create_workspace(ctx, name, public):
        r = ctx["session"].post("workspace", json={"name": name, "public": public,})
        exit_with(handle_request_error(r))

    @workspace.command(name="share", aliases=["s"])
    @click.argument("workspace_id")
    @click.argument("sharee_id")
    @click.option(
        "--permission",
        type=click.Choice(schemas.ShareType),
        default=schemas.ShareType.READ.value,
    )
    @click.option("--expire", type=click.DateTime())
    @click.pass_obj
    def create_workspace_share(ctx, workspace_id, sharee_id, permission, expire):
        body = {
            "workspace_id": workspace_id,
            "sharee_id": sharee_id,
            "permission": permission,
        }
        if expire:
            body["expiration"] = expire
        r = ctx["session"].post(f"share", json=body,)
        exit_with(handle_request_error(r))

    cli.add_command(workspace)
