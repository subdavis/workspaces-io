# WorkspacesIO

A dead-simple FastAPI server to manage workspaces and multi-user sharing within MinIO/S3.

## Concepts

* workspaces are directory-style keys in s3
* user access is brokered through short-lived STS credentials and S3 access policy
* users get a key for their own workspaces, and an additional key for each share
* users can interact with their data using the full power of `minio/mc` wrapped in smart token caching and switching.  Users can even move data between their owned and shared workspaces seamlessly by requesting new multi-workspace tokens on-the-fly.

Problems with this approach

* It's not clear how this could be packaged in a re-usable way for multiple applications.  Concrete implementations will no doubt want to attach additional data to users and workspaces (at minimum) and structuring the code to allow for extension of the base models isn't easy to do. [fastapi_users](https://github.com/frankie567/fastapi-users) attempted to do exactly this, but their implementation left much to be desired.
* For whatever reason, [you can't explicitly revoke STS credentials](https://stackoverflow.com/questions/47026661/explicitly-expire-tokens-acquired-from-aws-security-token-service).  That's how AWS does it so MinIO won't implement it either.  This means that share revocation has a big asterisk: anyone with outstanding credentials can continue to modify data in s3 until that share expires.

### Future work

* Support multiple MinIO, S3, and other compatible backends.
* Allow unprivileged users to bring in their own storage.
* Indexing file names and possibly text contents with ElasticSearch.
* Implement `nodes` , allowing multiple s3/minio/gcs/whatever backends.  Allow unprivileged users to introduce nodes into the workspace cluster.
* Implement `roots` , or a root path inside a bucket where workspaces-io manages all the content.  Roots must be created by node operators.
  + `public` type, that users can create public workspaces in, follow naming conventions
  + `private` type, that users can create private workspaces in, follow naming conventions
  + `unmanaged-public` type, that don't support traditional public/private.  This type is intended for "importing" existing data, and efficient for read-only operations.  They can still be edited, but if a user owns a workspace here, they need a workspace-specific key to manage it, which will eat into their token character limit.  This type is recommended for public read-only collections.
  + `unmanaged-private` type, similar to above, but with no token optimizations of any kind.  Good for bringing one-off workspaces into the application, but use sparingly, because read and write access require one-off token allocation.
* I still don't know how root-permissions will work.  What determines which users are permitted create privileges on a particular root?  How can a group of users all be root managers?  For now, all public and private roots have global create permissions.  Unmanaged roots have no create permissions, and workspaces in these roots must be crated or imported by the root's node operator.
* Implement `indexes` at the root level.   Workspaces are only indexed by virtue of which root they're in.   A server could theoretically have different levels of indexing on different roots, allowing users to allocate their workspaces based on the level of indexing they need.
* Implement `quotas` at multiple levels.  Users have an overall quota, a root-specific quota, and a workspace quota.  Quotas could be unique to individual users.  **QUOTAS are not enforceable** while a user holds a token.  If a user exceeds their quota, this will be noticed later by the notifier and future credentials requests will be blocked.  If it's not obvious by now, this system has a low tolerence/defense for bad faith actors.  Quotas are tools for systems administrators to prevent users from accidentally crippling resourcs.
  + To _really_ implement quotas and share revokes, some kind of layer 7 middleware would be necessary in front of minio.  You'd literall have to implement an http proxy to inspect every request's token headers.  That sounds exhausting.
  + I'd do it with something like https://github.com/elazarl/goproxy

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
fast-create-tables

# run dev server
# need host arg because minio must be able to post to the server
uvicorn workspacesio.asgi:app --host 0.0.0.0 --reload
```
