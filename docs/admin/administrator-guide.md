# Server Administrator Guide

## Getting Started

WorkspacesIO is an OpenID Oauth2 application.  It should support most OpenID auth providers.

* Auth0 (recommended)
* Google (tested)

You'll need to create an OAuth app if you intend to use more than the defalt root admin user.

## MinIO Setup

A minio root account cannot be used to create a Storage because it cannot be used for STS assume role.  Create a new user.

``` sh
# Create alias
mc alias set mybackend http://localhost:9000 minio minio1234
# Create user
mc admin user add mybackend backend backend1234
# Give user access to all buckets
mc admin policy set mybackend readwrite user=backend
```

## Server Config

Place an `.env` file in `docker/` with these variables.

| ENV Name | Default | description |
|----------|---------|-------------|
| `WIO_PUBLIC_NAME` | `http://localhost:8100/` | The public name of the workspaces server that clients can use
| `WIO_DATABASE_URL` | `postgresql:///wio` | postgres connection string
| `WIO_SECRET` | `fast` | hashing secret for sessions and other needs
| `WIO_ES_NODES` | `["http://localhost:9200"]` | JSON array of elasticsearch nodes
| `WIO_OIDC_NAME` | `auth0` | OpenID Connect provider
| `WIO_OIDC_CLIENT_ID` | none | OpenID Connect client id
| `WIO_OIDC_CLIENT_SECRET` | none | OpenID Connect client secret
| `WIO_OIDC_WELL_KNOWN` | none | OpenID Connect well known discovery endpoint
| `WIO_OIDC_ALGOS` | `["RS256"]` | JSON array of algos to use

...plus any configuration that FastAPI takes by default.

## Docker

``` sh
cd docker/
docker-compose up -d
```

Initialize the stack by running through the commands in `initialize.sh` .

# Debugging

https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPROFILEIMPORTTIME

``` bash
PYTHONPROFILEIMPORTTIME=1 wio
```