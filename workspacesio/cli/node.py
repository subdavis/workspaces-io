import click
from click_aliases import ClickAliasedGroup

from workspacesio.common import schemas

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

    @node.command(name="delete", aliases=["d"])
    @click.argument("node_id", type=click.STRING, required=True)
    @click.pass_obj
    def rm(ctx, node_id):
        r = ctx["session"].delete(f"node/{node_id}")
        exit_with(handle_request_error(r))

    @node.command(name="create", aliases=["c"])
    @click.argument("name", type=click.STRING)
    @click.argument("api_url", type=click.STRING)
    @click.argument("access_key_id", type=click.STRING)
    @click.argument("secret_access_key", type=click.STRING)
    @click.option("--region-name", type=click.STRING, default="us-east-1")
    @click.option("--sts-api-url", type=click.STRING)
    @click.option(
        "--role-arn",
        type=click.STRING,
        help="ARN for role to use during STS assume role.  Required for s3, Ignored for MinIO.  Make sure this role has NO permissions",
    )
    @click.pass_obj
    def register(
        ctx,
        name,
        api_url,
        access_key_id,
        secret_access_key,
        region_name,
        sts_api_url,
        role_arn,
    ):
        r = ctx["session"].post(
            "node",
            json={
                "name": name,
                "api_url": api_url,
                "access_key_id": access_key_id,
                "secret_access_key": secret_access_key,
                "region_name": region_name,
                "sts_api_url": sts_api_url,
                "assume_role_arn": role_arn,
            },
        )
        exit_with(handle_request_error(r))

    cli.add_command(node)
