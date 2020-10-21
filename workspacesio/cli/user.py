import click
from click_aliases import ClickAliasedGroup

from workspacesio.common import schemas

from . import config
from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @cli.group(name="user", cls=ClickAliasedGroup, aliases=["u"])
    def user():
        pass

    @user.command(name="list", aliases=["l", "ls"])
    @click.pass_obj
    def findusers(ctx):
        ctx = config.getctx(ctx)
        r = ctx.session.get(f"user")
        if r.ok:
            for user in r.json():
                userschema = schemas.UserDB(**user)
                click.secho(f"[{userschema.created}] ", fg="green", nl=False)
                click.secho(f"{userschema.id} ", fg="yellow", nl=False)
                click.secho(f"{userschema.username} ", fg="cyan", bold=True)
        else:
            exit_with(handle_request_error(r))
