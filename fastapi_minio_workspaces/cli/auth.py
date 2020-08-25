import click

from .util import exit_with, handle_request_error
from .config import save_config


def make(cli: click.Group):
    @click.command(name="login")
    @click.argument("email")
    @click.option("--password", prompt=True, hide_input=True)
    @click.pass_obj
    def login(ctx, email, password):
        conf = ctx["config"]
        r = ctx["session"].post(
            "auth/jwt/login", {"username": email, "password": password,}
        )
        if r.ok:
            token = r.json()["access_token"]
            click.echo(click.style("Login success", fg="green", bold=True))
            conf.token = token
            save_config(conf, ctx["configPath"])
        else:
            exit_with(handle_request_error(r))

    @click.command(name="register")
    @click.argument("email")
    @click.argument("username")
    @click.option("--password", prompt=True, hide_input=True)
    @click.pass_obj
    def register(ctx, email, password, username):
        r = ctx["session"].post(
            "auth/register",
            json={"email": email, "username": username, "password": password,},
        )
        exit_with(handle_request_error(r))

    cli.add_command(login)
    cli.add_command(register)
