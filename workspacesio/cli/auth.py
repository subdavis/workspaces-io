import webbrowser
from typing import cast

import click

from workspacesio.common import schemas

from . import config
from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @click.command(name="login")
    @click.option("--access-key", prompt=True)
    @click.option("--secret-key", prompt=True)
    @click.pass_obj
    def login(ctx, access_key, secret_key):
        ctx = config.getctx(ctx)
        r = ctx.session.get("user/me", auth=(access_key, secret_key))
        if r.ok:
            click.echo(click.style("Login success", fg="green", bold=True))
            ctx.config.access_key = access_key
            ctx.config.secret_key = secret_key
            config.save(ctx)
        else:
            exit_with(handle_request_error(r))

    @click.command(name="info")
    @click.pass_obj
    def me(ctx):
        ctx = config.getctx(ctx)
        r1 = ctx.session.get("user/me")
        if not r1.ok:
            exit_with(handle_request_error(r1))
        out = r1.json()
        out.update(ctx.config.dict())
        out.update({"configPath": ctx.configPath})
        exit_with(out)

    cli.add_command(login)
    cli.add_command(me)
