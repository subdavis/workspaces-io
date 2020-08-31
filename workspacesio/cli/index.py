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
        if r.ok:
            data = r.json()
            root_id = data["root_id"]
            bucket = data["root"]["bucket"]
            prefix = posixpath.join(data["root"]["base_path"], "/")
            commands = [
                # wehook ID should come from ROOT, not index.  You only want to subscribe to events once.
                f"export ALIAS=local"
                f"mc admin config set $ALIAS notify_webhook:{str(public_index.id)} endpoint=http://varrock:8000/api/minio/events",
                f"mc event add $ALIAS/{public_index.s3_bucket} arn:minio:sqs::{str(public_index.id)}:webhook --prefix {public_index.s3_root} --event delete,put",
            ]
        else:
            exit_with(handle_request_error(r))

    cli.add_command(index)
