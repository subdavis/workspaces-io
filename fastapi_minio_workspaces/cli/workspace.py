import click

from fastapi_minio_workspaces import schemas

from .util import exit_with, handle_request_error


@click.group(name="workspace")
def workspace():
    pass


@workspace.command(name="list")
@click.pass_obj
def list_workspaces(ctx):
    r = ctx["session"].get("workspace")
    exit_with(handle_request_error(r))


@workspace.command(name="create")
@click.argument("name")
@click.option("--public/--private", default=False, is_flag=True)
@click.pass_obj
def create_workspace(ctx, name, public):
    r = ctx["session"].post("workspace", json={"name": name, "public": public,})
    exit_with(handle_request_error(r))


@workspace.command(name="share")
@click.argument("workspace_id")
@click.argument("sharee_id")
@click.option(
    "--permission", type=click.Choice(schemas.ShareType), default=schemas.ShareType.READ
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
    r = ctx["session"].post(f"share", json=body,)
    exit_with(handle_request_error(r))


@workspace.command(name="fetch-token")
@click.option("--workspace-id", type=click.STRING, default=None)
@click.pass_obj
def create_workspace_token(ctx, workspace_id):
    body = {}
    if workspace_id:
        body["workspace_id"] = workspace_id
    r = ctx["session"].post("token", json=body)

    if r.ok:
        response = r.json()
        access_key_id = response["access_key_id"]
        secret_access_key = response["secret_access_key"]
        session_token = response["session_token"]

        click.echo(click.style(f"export AWS_ACCESS_KEY_ID={access_key_id}"))
        click.echo(click.style(f"export AWS_SECRET_ACCESS_KEY={secret_access_key}"))
        click.echo(click.style(f"export AWS_SESSION_TOKEN={session_token}"))
        click.echo(click.style(f"alias workspace='aws s3api --bucket fast"))
    else:
        exit_with(handle_request_error(r))
