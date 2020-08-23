import click

from .util import exit_with, handle_request_error


@click.command(name="login")
@click.argument("email")
@click.option("--password", prompt=True, hide_input=True)
@click.pass_obj
def login(ctx, email, password):
    r = ctx["session"].post(
        "auth/jwt/login", {"username": email, "password": password,}
    )
    if r.ok:
        token = r.json()["access_token"]
        click.echo(click.style("Login success\n", fg="green", bold=True))
        click.echo(f"export FMI_TOKEN={token}")
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
