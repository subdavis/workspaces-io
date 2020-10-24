# User Getting Started Guide

This section is intended as a user guide and assumes you have a **running server**.  See the server config docs for help getting an instance running.

* WorkspacesIO has a web app for file browsing, search, etc.
* All administrative tasks and config are done through the `wio` cli.

## Installation

``` bash
# with pip
pip install workspacesio-cli

# with pipx
pipx install workspacesio-cli

# verify installation
wio --version
```

## Client configuration

To get an API token for the cli, visit **http(s)://yourserver.com/app/** and visit the token section.

``` bash
wio --api-url http://yourserver.com/api \
    login \
    --access-key {access_key} \
    --secret-key {secret_key}
```

Verify the login.

``` bash
wio info
```

Note the location of your configuration file.  Your credentials are stored unencrypted.

## Common commands

``` bash
# Show the help
wio --help

# Show subcommand help
wio <command> --help

# List your workspaces
wio workspace ls

# List your nodes
wio node ls
```

# Managing workspaces

