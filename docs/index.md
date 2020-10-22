# WorkspacesIO

![Workspace](images/workspacesio-logo-circle.png)

> Better than your NAS, probably

-----------

**Documentation**: [https://workspacesio.app/](https://workspacesio.app/)

**Source Code**: [https://github.com/subdavis/workspacesio](https://github.com/subdavis/workspaces-io)

-----------

## Key Features

* **Non-invasive import** and **indexing** of your existing data.  We leave your data just as it is on-disk.
* Simple permissions management. `wio create` to make new workspaces. `wio share` to share them with others.
* **Low-friction access** to your data.  WorkspacesIO grants **STS credentials** so that users can connect directly to minio for listing, upload, and download operations.  You can even continue to use `minio/mc` or `boto3` , with some caveats.
* Permissions-aware indexing and aggregation across the system.
* Hub-and-spoke architecture.  Run a MinIO node wherever you have data, and it will be available through Workspaces.  Even **regular users** can introduce new nodes into the system and retain full control of their data.
