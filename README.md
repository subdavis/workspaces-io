<p align="center">
  <img src="docs/images/workspacesio-logo-circle.png" width="640px">
</p>

> It's gonna kill your NAS

A dead-simple [FastAPI](https://fastapi.tiangolo.com/) service to manage multi-user permissions and indexing for S3 and MinIO.

## Features

* **Non-invasive import** and **indexing** of your existing data.  We leave your data just as it is on-disk.
* Simple permissions management. `wio create` to make new workspaces. `wio share` to share them with others.
* **Low-friction access** to your data.  WorkspacesIO grants **STS credentials** so that users can connect directly to minio for listing, upload, and download operations.  You can even continue to use `minio/mc` or `boto3` , with some caveats.
* Permissions-aware indexing and aggregation across the system.
* Hub-and-spoke architecture.  Run a MinIO node wherever you have data, and it will be available through Workspaces.  Even **regular users** can introduce new nodes into the system and retain full control of their data.

## Philosophy

Data management should come to users and the places they already have data.  If your team wants to use powerful industry-standard tools like MinIO and ElasticSearch, but needs permissions management, WorkspacesIO might be an option.

## Caveats

For whatever reason, [you can't explicitly revoke STS credentials](https://stackoverflow.com/questions/47026661/explicitly-expire-tokens-acquired-from-aws-security-token-service).  That's how AWS does it so MinIO won't implement it either.  This means that share revocation has a big asterisk: anyone with outstanding credentials can continue to modify data in s3 until that share expires.

## FAQ

> What's a workspace?

It's just a folder.  Users manage the hierarchy within.  Permissions are managed at the workspace level.  You can search for workspace contents and share individual objects, but these are features of elasticsearch and minio, respectively.

> Who is this for?

WorkspacesIO is for organizations that need to manage large quantities of slow-moving data of the sort that laboratories and research teams accumulate.  Think Samba, CIFS, FTP, SSHFS.  WorksapcesIO can map your existing data while you transition, or run side-by-side forever.

> What if I want to share a single file?

There's always pre-signed URLs to email a colleague.  But you shouldn't think of this like Google Drive; WorkspacesIO isn't for slide decks.

> Why not just MinIO?

MinIO's multi-user management is great when all users a) need their own space or b) can share everything, but it's cumbersome for dynamic permissions management.  WorkspacesIO gives you Role-based access control.

> Can I just try it?  What if I hate it?

Because it doesn't modify the structure of your data on disk, WorkspacesIO is easy to try.

> Multiple nodes?  Isn't that just MinIO Distributed Mode?

Not at all.  MinIO's Distributed Mode solves an operational and deeply technical problem.  It allows for data redundancy and high availability.  WorkspacesIO solves a bureaucratic problem.  You've got data on different servers and workstations in different locations.  You can't reasonably migrate it all into the same storage cluster, but you want to provide read/write/search to certain authenticated users across your org.

## Concepts In Depth

### Workspaces and Roots

Workspaces are directory-style prefixes in s3, typically following the convention `{bucket}/{root_prefix}/{username}/{workspace_name}` .

A workspace root is a prefix inside a bucket where workspaces-io manages all sub-keys, a boundary of control.  Roots must be created by node operators.

* `public` type, that users can create public workspaces in, follow regular naming conventions
* `private` type, that users can create private workspaces in, follow naming conventions
* `unmanaged-public` type, that don't support traditional public/private.  This type is intended for "importing" existing data, and efficient for read-only operations.  They can still be edited, but if a user owns a workspace here, they need a workspace-specific key to manage it, which will eat into their token character limit.  This type is recommended for public read-only collections.
* `unmanaged-private` type, similar to above, but with no token optimizations of any kind.  Good for bringing one-off workspaces into the application, but use sparingly, because read and write access require one-off token allocation.

### Sharing and Authentication

* user access is brokered through short-lived STS credentials and S3 access policy
* users get a key for their own workspaces, and an additional key for each share.  A sort of vector key is produced when a user wants to perform an operation on multiple key realms within the same node.  For example, moving data from an owned private workspace to a shared public workspace would require a special combined key.  WorkspacesIO hides this detail.

## Roadmap

* Web client for data exploration.
* I still don't know how root-permissions will work.  What determines which users are permitted create privileges on a particular root?  How can a group of users all be root managers?  For now, all public and private roots have global create permissions.  Unmanaged roots have no create permissions, and workspaces in these roots must be crated or imported by the root's node operator.
* Implement `indexes` at the root level.   Workspaces are only indexed by virtue of which root they're in.   A server could theoretically have different levels of indexing on different roots, allowing users to allocate their workspaces based on the level of indexing they need.
* Implement `quotas` at multiple levels.  Users have an overall quota, a root-specific quota, and a workspace quota.  Quotas could be unique to individual users.  **QUOTAS are not enforceable** while a user holds a token.  If a user exceeds their quota, this will be noticed later by the notifier and future credentials requests will be blocked.  If it's not obvious by now, this system has a low tolerence/defense for bad faith actors.  Quotas are tools for systems administrators to prevent users from accidentally crippling resourcs.
  + To _really_ implement quotas and share revokes, some kind of layer 7 middleware would be necessary in front of minio.  You'd literall have to implement an http proxy to inspect every request's token headers.  That sounds exhausting.
  + I'd do it with something like https://github.com/elazarl/goproxy

## Server Config

| ENV Name | Default | description |
|----------|---------|-------------|
| `WIO_SECRET` | `fast` | hashing secret for db passwords |
| `WIO_PUBLIC_NAME` | `http://localhost:8100` | how clients connect to the server |
| `WIO_DATABASE_URL` | `postgresql://wio:workspaces@localhost:5555/wio` | postgres connection string |
| `WIO_ELASTICSEARCH_NODE_1` | `http://localhost:9200` | elasticsearch connection string |
| `WEB_CONCURRENCY` | none | how many fastapi worker threads to run |

## Usage

Example of current capabilities

``` sh
wio register email@domain.com user
wio login email@domain.com

wio workspace create myspace
wio workspace share <workspace_id> <other_user_id>
```

Future plans for integration with mc, generally involve wrapping and inspecting arguments to dynamically generate a set of credentials meeting the dependencies of the action.

Support `ls, mv, cp, rm, diff, cat, tree, head, mirror, watch` . Minio Client should be available on your `$PATH` as `mc` .

``` sh
# list the contents of a workspace
wio mc ls myworkspace

# move some data from your workspace to a shared workspace
wio mc mv myworkspace/file.txt sharedworkspace/file.txt

# list public workspaces
wio w ls --public

# list data in a public workspace subfolder
wio mc ls ownername/workspacename/subfolder/
```

### Referring to workspaces

You can refer to workspaces either

* directly by `workspacename/`
* through their owner by `owner/workspacename/`

## MinIO Setup

boto3 client can be used for `s3` and `sts` access, but a non-root minio user must be created.

``` sh
# Create alias
mc alias set local http://localhost:9000 minio minio1234
# Create user
mc admin user add local backend backend1234
# Give user access to all buckets
mc admin policy set local readwrite user=backend
```

## Dev setup

``` sh
# run dependent services
docker-compose up -d

# install
virtualenv -p python3 venv/
venv/bin/activate

pip3 install -e .
pip3 install -r dev.requirements.txt

# run db migrations
workspaces-create-tables

# run dev server
# need host arg because minio must be able to post to the server
uvicorn workspacesio.asgi:app --host 0.0.0.0 --port 8100 --reload
```

## Docker

``` sh
docker-compose up
```

Initialize the stack by running through the commands in `initialize.sh` .

# Debugging

https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPROFILEIMPORTTIME

``` 
PYTHONPROFILEIMPORTTIME=1 wio
```
