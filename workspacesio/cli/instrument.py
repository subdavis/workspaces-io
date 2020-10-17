import click
from click_aliases import ClickAliasedGroup

from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @cli.group(name="instrument", cls=ClickAliasedGroup)
    def instrument():
        pass

    @instrument.command(name="start")
    @click.argument("tag", type=click.STRING)
    @click.pass_obj
    def start(ctx, tag):
        pass

    @instrument.command(name="end")
    @click.argument("tag", type=click.STRING)
    @click.pass_obj
    def end(ctx, tag):
        pass
