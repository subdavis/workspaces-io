import click
from click_aliases import ClickAliasedGroup

from workspacesio.schemas import S3TokenDB

from .config import save_config
from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @cli.group(name="token", cls=ClickAliasedGroup, aliases=["t"])
    def token():
        pass

    @token.command(name="fetch", aliases=["f"])
    @click.option("--workspace-id", type=click.STRING, default=None)
    @click.pass_obj
    def create_token(ctx, workspace_id):
        body = {}
        if workspace_id:
            body["workspace_id"] = workspace_id
        r = ctx["session"].post("token", json=body)

        if r.ok:
            response = S3TokenDB(**r.json())
            ctx["config"].s3tokens[str(response.id)] = response
            save_config(ctx["config"], ctx["configPath"])
            click.echo(click.style("Token fetch success\n", fg="green", bold=True))
        else:
            exit_with(handle_request_error(r))

    @token.command(name="list", aliases=["l"])
    @click.pass_obj
    def list_token(ctx):
        r = ctx["session"].get("token")
        exit_with(handle_request_error(r))

    @token.command(name="delete", aliases=["d"])
    @click.argument("token_id")
    @click.pass_obj
    def delete_token(ctx, token_id):
        r = ctx["session"].delete(f"token/{token_id}")
        exit_with(handle_request_error(r))

    cli.add_command(token)
