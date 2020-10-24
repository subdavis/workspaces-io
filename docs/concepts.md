# Concepts

WorkspacesIO provides web and command-line data management.

* MinIO (or S3) store data.
* Elasticsearch + a python crawler provide indexing
* [Filestash](https://filestash.app) provides web based data management
* A FastAPI + SQLAlchemy service keeps track of permissions and acts as a broker for STS credentials.

## Models

### Storage Node

A storage node is a storage backend, such as a single MinIO instance or AWS S3 account.  Any system user can add a new storage node.

### Workspace Root

A workspace root is a bucket (and optional prefix) within a storage backend where WorkspacesIO is responsible for managing data.

* public and private type roots **must be used exclusively with workspaces**.  They rely on a prefix naming convention that is primarily an optimization for IAM Policy generation.
  * A user's private workspaces can be placed in any private root.
  * A user's public workspaces can be placed in any public root.
* unmanaged roots, which are ideal for mapping existing data into workspaces.  Unmanaged roots can contain workspaces as well as data not managed by WorkspacesIO.  Workspaces inside of unmanaged roots have no special properties: they can be shared and edited.

### Workspace

A workspace is location (prefix) in an s3 bucket managed by WorkspacesIO.  Users can create workspaces, upload data to them, share them, and index them.  Individual objects can be shared read-only using pre-signed URLs, but WorkspacesIO is intended primarily for managing permissions for data collections, not individual data objects, similar to seafile.

## Authorization process

What happens when you try to list a directory or upload a file?

```
wio mc ls workspacename/
```

* A request is made to the WorkspacesIO backend token search endpoint, containing the arguments to `ls`
* WorkspacesIO identifies `workspacename/` as a valid workspace name, and searches for matching STS credentials.
* If valid credentials aren't found, the backend issues an STS `AssumeRole` to the storage node backend, which results in an `AccessKey`, `SecretKey`, and `SessionToken`.
* The backend caches these credentials, which were generated specially for `workspacename/`, and passes them back to the client
* The client passes these credentials to MinIO Client (`mc`) through environment variables.


## Roadmap

* I still don't know how root-permissions will work.  What determines which users are permitted create privileges on a particular root?  How can a group of users all be root managers?  For now, all public and private roots have global create permissions.  Unmanaged roots have no create permissions, and workspaces in these roots must be crated or imported by the root's node operator.
* Implement `indexes` at the root level.   Workspaces are only indexed by virtue of which root they're in.   A server could theoretically have different levels of indexing on different roots, allowing users to allocate their workspaces based on the level of indexing they need.
* Implement `quotas` at multiple levels.  Users have an overall quota, a root-specific quota, and a workspace quota.  Quotas could be unique to individual users.  **QUOTAS are not enforceable** while a user holds a token.  If a user exceeds their quota, this will be noticed later by the notifier and future credentials requests will be blocked.  If it's not obvious by now, this system has a low tolerence/defense for bad faith actors.  Quotas are tools for systems administrators to prevent users from accidentally crippling resourcs.
  + To _really_ implement quotas and share revokes, some kind of layer 7 middleware would be necessary in front of minio.  You'd literall have to implement an http proxy to inspect every request's token headers.  That sounds exhausting.
  + I'd do it with something like https://github.com/elazarl/goproxy