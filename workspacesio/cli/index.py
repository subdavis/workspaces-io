import click

from .config import save_config
from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @cli.group(name="index")
    def index():
        pass

    @index.command(name="create")
    @click.pass_obj
    def register(ctx):
        r = ctx["session"].post("index")
        exit_with(handle_request_error(r))

    cli.add_command(index)
