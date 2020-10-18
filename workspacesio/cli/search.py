import click

from . import config
from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @cli.command(name="search")
    @click.argument("query", type=click.STRING)
    @click.pass_obj
    def search(ctx, query):
        ctx = config.getctx(ctx)
        r = ctx.session.get(
            "search",
            params={"q": query},
        )
        if not r.ok:
            exit_with(handle_request_error(r))
        for result in r.json()["hits"]["hits"]:
            click.secho(
                f'{result["_source"]["owner_name"]}/', fg="cyan", bold=True, nl=False
            )
            click.secho(
                f'{result["_source"]["workspace_name"]}',
                fg="cyan",
                bold=True,
                nl=False,
            )
            click.secho(result["_source"]["path"])

    cli.add_command(search)
