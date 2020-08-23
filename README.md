# FastAPI MinIO Workspaces

A simple FastAPI server to manage workspaces and multi-user sharing within MinIO.

## Concepts

* workspaces are directory-style keys in s3
* user access is brokered through short-lived STS credentials and S3 access policy
* users get a key for their own workspaces, and an additional key for each share

Problems with this approach

* It's not clear how this could be packaged in a re-usable way for multiple applications.  Concrete implementations will no doubt want to attach additional data to users and workspaces (at minimum) and structuring the code to allow for extension of the base models isn't easy to do. [fastapi_users](https://github.com/frankie567/fastapi-users) attempted to do exactly this, but their implementation left much to be desired.
* For whatever reason, [you can't explicitly revoke STS credentials](https://stackoverflow.com/questions/47026661/explicitly-expire-tokens-acquired-from-aws-security-token-service).  That's how AWS does it so MinIO won't implement it either.  This means that share revocation has a big asterisk: anyone with outstanding credentials can continue to modify data in s3 until that share expires.

## Usage

Example of current capabilities

``` sh
fmm register email@domain.com user
fmm login user

fmm workspace create myspace
fmm token fetch
fmm s3 list <workspace_id>
fmm workspace share <workspace_id> <other_user_id>
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
minws

# run dev server
uvicorn fastapi_minio_workspaces.asgi:app --reload
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
