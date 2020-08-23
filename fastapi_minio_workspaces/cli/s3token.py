import click
from click_aliases import ClickAliasedGroup

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
            response = r.json()
            access_key_id = response["access_key_id"]
            secret_access_key = response["secret_access_key"]
            session_token = response["session_token"]

            click.echo(
                click.style(
                    f"export AWS_ACCESS_KEY_ID={access_key_id}", bold=True, fg="green"
                )
            )
            click.echo(
                click.style(
                    f"export AWS_SECRET_ACCESS_KEY={secret_access_key}",
                    bold=True,
                    fg="green",
                )
            )
            click.echo(
                click.style(
                    f"export AWS_SESSION_TOKEN={session_token}", bold=True, fg="green"
                )
            )

            exit_with(handle_request_error(r))
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
