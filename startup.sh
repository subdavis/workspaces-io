#!/bin/sh

workspaces-create-tables
exec uvicorn workspacesio.asgi:app --host 0.0.0.0 --port 8000
