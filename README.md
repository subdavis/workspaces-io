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

## Usage

Example of current capabilities

``` sh
wio register email@domain.com user
wio login user

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
uvicorn workspacesio.asgi:app --reload
```

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
