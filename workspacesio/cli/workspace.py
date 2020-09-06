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
    @cli.group(name="workspace", cls=ClickAliasedGroup, aliases=["w"])
    def workspace():
        pass

    @workspace.command(name="list", aliases=["ls", "l"])
    @click.option("--name", type=click.STRING, required=False)
    @click.option("--like", type=click.STRING, required=False)
    @click.option("--public", is_flag=True)
    @click.pass_obj
    def list_workspaces(ctx, name, like, public):
        params = {"public": public}
        if name:
            params["name"] = name
        if like:
            params["like"] = like
        r = ctx["session"].get("workspace", params=params)
        if r.ok:
            for ws in r.json():
                root = ws["root"]["base_path"]
                scope = ws["root"]["root_type"]
                click.secho(f"[{ws['created']}] ", fg="green", nl=False)
                click.secho(f"{ws['id']} ", fg="yellow", nl=False)
                click.secho(
                    f"{root}/{ws['owner']['username']}/{ws['name']}/ ",
                    fg="cyan",
                    bold=True,
                    nl=False,
                )
                click.secho(f"({scope})", fg="bright_black")
        else:
            exit_with(handle_request_error(r))

    @workspace.command(name="create", aliases=["c"])
    @click.argument("name")
    @click.option("--public/--private", default=False, is_flag=True)
    @click.option("--unmanaged", default=False, is_flag=True)
    @click.option("--node-name", type=click.STRING, default=None)
    @click.pass_obj
    def create_workspace(ctx, name, public, unmanaged, node_name):
        r = ctx["session"].post(
            "workspace",
            json={
                "name": name,
                "public": public,
                "unmanaged": unmanaged,
                "node_name": node_name,
            },
        )
        exit_with(handle_request_error(r))

    @workspace.command(name="delete")
    @click.argument("workspace_id", type=click.STRING)
    @click.pass_obj
    def delete_workspace(ctx, workspace_id):
        r = ctx["session"].delete(f"workspace/{workspace_id}")
        exit_with(handle_request_error(r))

    @workspace.command(name="share", aliases=["s"])
    @click.argument("workspace_id")
    @click.argument("sharee_id")
    @click.option(
        "--permission",
        type=click.Choice(schemas.ShareType),
        default=schemas.ShareType.READ.value,
    )
    @click.option("--expire", type=click.DateTime())
    @click.pass_obj
    def create_workspace_share(ctx, workspace_id, sharee_id, permission, expire):
        body = {
            "workspace_id": workspace_id,
            "sharee_id": sharee_id,
            "permission": permission,
        }
        if expire:
            body["expiration"] = expire
        r = ctx["session"].post(
            f"share",
            json=body,
        )
        exit_with(handle_request_error(r))

    cli.add_command(workspace)

    @workspace.command(name="index")
    @click.argument("workspace_id", type=click.STRING)
    @click.option(
        "--minio-mount",
        type=click.Path(dir_okay=True, exists=True),
        help="Path to minio mount on local disk",
    )
    @click.pass_obj
    def index_workspace(ctx, workspace_id, minio_mount):
        r = ctx["session"].get(f"workspace/{workspace_id}")
        if not r.ok:
            exit_with(handle_request_error(r))
        workspace = schemas.WorkspaceDB(**r.json())
        r = ctx["session"].post(
            "node/root/import", json={"root_id": str(workspace.root_id)}
        )
        if not r.ok:
            exit_with(handle_request_error(r))
        rdata = schemas.RootImport(**r.json())
        pbar = tqdm([workspace])
        for w in pbar:
            for batch in minio_buffer_objects(
                minio_recursive_generate_objects(
                    node=rdata.node, root=rdata.root, workspace=w
                ),
                buffer_size=100,
            ):
                documents: List[indexing_schemas.IndexDocumentBase] = []
                for obj in batch:
                    doc = minio_transform_object(workspace=w, root=rdata.root, obj=obj)
                    if minio_mount:
                        additional_indexes(
                            root=rdata.root, workspace=w, doc=doc, mount=minio_mount
                        )
                    documents.append(doc)
                payload = indexing_schemas.IndexBulkAdd(
                    documents=documents,
                    workspace_id=w.id,
                )
                ctx["session"].post(
                    "index_bulk",
                    data=payload.json(),
                )
