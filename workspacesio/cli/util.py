import json
from collections.abc import Iterable
from json.decoder import JSONDecodeError
from typing import List

import click
from requests import Response


def handle_request_error(r: Response) -> dict:
    if not r.ok:
        # TODO: inspect content-type to infer this
        error_text = r.text
        try:
            error_text = r.json()
        except ValueError:
            pass

        headers = dict(r.request.headers)
        headers.pop("Authorization", None)
        body = str(r.request.body)
        try:
            body = json.loads(body)
        except JSONDecodeError:
            pass

        if r.status_code == 401:
            return {"error": "You are not logged in."}

        return {
            "context": {
                "url": r.url,
                "method": r.request.method,
                "status": r.status_code,
                "body": body,
                "headers": headers,
            },
            "error": error_text,
        }
    return {"response": r.json()}


def exit_with(out: dict):
    if out.get("error"):
        click.secho(json.dumps(out, indent=2, sort_keys=True), fg="red")
        exit(1)
    click.echo(json.dumps(out, indent=2, sort_keys=True))
    exit(0)
