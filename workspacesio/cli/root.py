import click
from click_aliases import ClickAliasedGroup

from workspacesio import schemas

from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @cli.group(name="root", cls=ClickAliasedGroup, aliases=["r"])
    def root():
        pass

    @root.command(name="list", aliases=["l", "ls"])
    @click.option("--node-name", type=click.STRING)
    @click.pass_obj
    def list_roots(ctx, node_name):
        r = ctx["session"].get("node/root", params={"node_name": node_name})
        exit_with(handle_request_error(r))

    @root.command(name="create", aliases=["c"])
    @click.argument("bucket", type=click.STRING)
    @click.argument("node_name", type=click.STRING)
    @click.option("--base-path", type=click.STRING, default="")
    @click.option(
        "--root-type",
        type=click.Choice(schemas.RootType),
        default=schemas.RootType.PRIVATE.value,
    )
    @click.pass_obj
    def create_root(ctx, bucket, node_name, base_path, root_type):
        r = ctx["session"].post(
            "node/root",
            json={
                "bucket": bucket,
                "node_name": node_name,
                "base_path": base_path,
                "root_type": root_type,
            },
        )
        exit_with(handle_request_error(r))

    @root.command(name="import", help="Import all workspaces in a root.")
    @click.argument("root_id")
    @click.option(
        "--local-path",
        type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
        help="""
        path to where minio is mounted on the local disk. If this is not provided,
        credentials for the parent node will be retrieved from workspacesio and bytes
        will transfer over the network""",
    )
    @click.pass_context
    def import_all_workspaces(ctx, root_id, local_base_path):
        pass

    cli.add_command(root)
