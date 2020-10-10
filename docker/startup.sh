#!/bin/sh

if [ -n "${0+set}" ]; then
  pip install --no-deps .
fi

workspaces-create-tables
uvicorn workspacesio.asgi:app --host 0.0.0.0 --port 8100 $@
