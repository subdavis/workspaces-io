import click
from click_aliases import ClickAliasedGroup

from .config import save_config
from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @cli.group(name="node", cls=ClickAliasedGroup, aliases=["n"])
    def node():
        pass

    @node.command(name="list", aliases=["l", "ls"])
    @click.pass_obj
    def ls(ctx):
        r = ctx["session"].get("node")
        exit_with(handle_request_error(r))

    @node.command(name="create", aliases=["c"])
    @click.argument("name", type=click.STRING)
    @click.argument("api_url", type=click.STRING)
    @click.pass_obj
    def register(ctx, name, api_url):
        r = ctx["session"].post("node", json={"name": name, "api_url": api_url,})
        exit_with(handle_request_error(r))

    cli.add_command(node)
