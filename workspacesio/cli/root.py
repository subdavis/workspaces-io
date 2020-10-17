import click
from click_aliases import ClickAliasedGroup

from workspacesio.common import schemas

from . import config
from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @cli.group(name="root", cls=ClickAliasedGroup, aliases=["r"])
    def root():
        pass

    @root.command(name="list", aliases=["l", "ls"])
    @click.option("--node-name", type=click.STRING)
    @click.pass_obj
    def list_roots(ctx, node_name):
        r = ctx["session"].get("root", params={"node_name": node_name})
        exit_with(handle_request_error(r))

    @root.command(name="create", aliases=["c"])
    @click.argument("bucket", type=click.STRING)
    @click.argument("node_name", type=click.STRING)
    @click.option("--base-path", type=click.STRING, default="")
    @click.option(
        "--root-type",
        type=click.Choice(schemas.RootType),
        default=schemas.RootType.PRIVATE.value,
    )
    @click.pass_obj
    def create_root(ctx, bucket, node_name, base_path, root_type):
        r = ctx["session"].post(
            "root",
            json={
                "bucket": bucket,
                "node_name": node_name,
                "base_path": base_path,
                "root_type": root_type,
            },
        )
        exit_with(handle_request_error(r))

    @root.command(name="delete", aliases=["d"])
    @click.argument("root_id", type=click.STRING)
    @click.pass_obj
    def delete_root(ctx, root_id):
        r = ctx["session"].delete(f"root/{root_id}")
        exit_with(handle_request_error(r))

    @root.command(name="import", help="Import all workspaces in a root.")
    @click.argument("root_id")
    @click.option("--index-all", is_flag=True)
    @click.pass_obj
    def import_all_workspaces(ctx, root_id, index_all):
        # Dynamic, expensive imports
        from workspacesio.common import producers

        ctx = config.getctx(ctx)
        r = ctx.session.post(f"root/{root_id}/import")
        if not r.ok:
            exit_with(handle_request_error(r))
        rdata = schemas.RootCredentials(**r.json())
        root_contents = producers.minio_list_root_children(
            node=rdata.node, root=rdata.root
        )
        workspace_list: List[schemas.WorkspaceDB] = []
        for folder in root_contents:
            prefix = folder.object_name.lstrip(rdata.root.base_path).strip("/")
            if len(prefix) > 0:
                print(f"Discovered {prefix}")
                workspace = ctx.session.post(
                    "workspace",
                    json={
                        "name": prefix,
                        "public": False,
                        "unmanaged": True,
                        "base_path": prefix,
                        "node_name": rdata.node.name,
                        "root_id": str(rdata.root.id),
                    },
                )
                if not workspace.ok and workspace.status_code != 409:
                    exit_with(handle_request_error(workspace))
                workspace_list.append(schemas.WorkspaceDB(**workspace.json()))

    @root.command(
        name="import-workspace", help="Import a particular prefix as a workspace."
    )
    @click.argument("root_id", type=click.STRING)
    @click.argument("--base-path", type=click.STRING, default="")
    def import_workspace(ctx, root_id, base_path):
        pass

    cli.add_command(root)
