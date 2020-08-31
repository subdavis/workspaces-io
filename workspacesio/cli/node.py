import click
from click_aliases import ClickAliasedGroup

from workspacesio import schemas

from .config import save_config
from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @cli.group(name="node", cls=ClickAliasedGroup, aliases=["n"])
    def node():
        pass

    @node.command(name="list", aliases=["l", "ls"])
    @click.pass_obj
    def ls(ctx):
        r = ctx["session"].get("node")
        if r.ok:
            for node in r.json():
                api_url = node["api_url"]
                click.secho(f"[{node['created']}] ", fg="green", nl=False)
                click.secho(f"{node['id']} ", fg="yellow", nl=False)
                click.secho(f"{api_url} ", fg="bright_black", nl=False)
                click.secho(f"{node['name']}", fg="cyan", bold=True)
        else:
            exit_with(handle_request_error(r))

    @node.command(name="create", aliases=["c"])
    @click.argument("name", type=click.STRING)
    @click.argument("api_url", type=click.STRING)
    @click.argument("access_key_id", type=click.STRING)
    @click.argument("secret_access_key", type=click.STRING)
    @click.option("--region-name", type=click.STRING, default="us-east-1")
    @click.pass_obj
    def register(ctx, name, api_url, access_key_id, secret_access_key, region_name):
        r = ctx["session"].post(
            "node",
            json={
                "name": name,
                "api_url": api_url,
                "access_key_id": access_key_id,
                "secret_access_key": secret_access_key,
                "region_name": region_name,
            },
        )
        exit_with(handle_request_error(r))

    @node.command(name="create-root", aliases=["croot"])
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

    cli.add_command(node)
