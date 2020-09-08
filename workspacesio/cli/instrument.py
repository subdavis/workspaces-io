import datetime
import json
from typing import List

import click
from click_aliases import ClickAliasedGroup
from tqdm import tqdm

from workspacesio import schemas
from workspacesio.indexing import schemas as indexing_schemas
from workspacesio.indexing.producers import (
    additional_indexes,
    minio_buffer_objects,
    minio_recursive_generate_objects,
    minio_transform_object,
)

from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @cli.group(name="instrument")
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
