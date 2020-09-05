import click
from click_aliases import ClickAliasedGroup
from datetime import datetime
from workspacesio import schemas

from .config import save_config
from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @cli.group(name="token", cls=ClickAliasedGroup, aliases=["t"])
    def token():
        pass

    @token.command(name="fetch", aliases=["f"])
    @click.argument("workspaces", type=click.STRING, nargs=-1)
    @click.pass_obj
    def create_token(ctx, workspaces):
        if len(workspaces) == 0:
            return
        r = ctx["session"].post("token/search", json={"search_terms": workspaces})
        if r.ok:
            response = schemas.S3TokenSearchResponse(**r.json())
            for node, token in response.tokens:
                click.secho(
                    f"Credentials for {[w.name for w in token.workspaces]} @  {node.api_url}",
                    fg="green",
                )
                click.secho(
                    f"Expires in {token.expiration - datetime.utcnow()}\n", fg="yellow"
                )
                click.secho(f"export AWS_ACCESS_KEY_ID={token.access_key_id}")
                click.secho(f"export AWS_SECRET_ACCESS_KEY={token.secret_access_key}")
                click.secho(f"export AWS_SESSION_TOKEN={token.session_token}\n")
        else:
            exit_with(handle_request_error(r))

    @token.command(name="list", aliases=["l", "ls"])
    @click.pass_obj
    def list_token(ctx):
        r = ctx["session"].get("token")
        exit_with(handle_request_error(r))

    @token.command(name="delete", aliases=["d"])
    @click.option("--all", is_flag=True)
    @click.argument("token_id", required=False)
    @click.pass_obj
    def delete_token(ctx, all, token_id):
        if all:
            r = ctx["session"].delete("token")
        else:
            r = ctx["session"].delete(f"token/{token_id}")
        exit_with(handle_request_error(r))

    cli.add_command(token)
