import posixpath

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
        r2 = ctx["session"].get("info")
        if r.ok and r2.ok:
            data = r.json()
            infodata = r2.json()
            root_id = data["root_id"]
            bucket = data["root"]["bucket"]
            prefix = posixpath.join(data["root"]["base_path"], "/")
            server = data["root"]["api_url"]
            endpoint_base = infodata["public_address"]
            commands = [
                # wehook ID should come from ROOT, not index.  You only want to subscribe to events once.
                f"export ALIAS=local"
                f"mc admin config set $ALIAS notify_webhook:{root_id} endpoint={endpoint_base}/api/minio/events",
                f"mc event add $ALIAS/{bucket} arn:minio:sqs::{root_id}:webhook --prefix {prefix} --event delete,put",
            ]
        else:
            exit_with(handle_request_error(r))

    cli.add_command(index)
