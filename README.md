<p align="center">
  <img src="docs/images/workspacesio-logo-circle.png" width="640px">
</p>

> Better than your NAS, probably

A dead-simple [FastAPI](https://fastapi.tiangolo.com/) service to manage multi-user permissions and indexing for S3 and MinIO.

## Documentation

* **[General Docs](https://workspacesio.subdavis.com/)**
* **[Administrator Docs](https://workspacesio.subdavis.com/admin/administrator-guide/)**

## Features

* **Non-invasive import** and **indexing** of your existing data.  We leave your data just as it is on-disk.
* Simple permissions management. `wio create` to make new workspaces. `wio share` to share them with others.
* **Low-friction access** to your data.  WorkspacesIO grants **STS credentials** so that users can connect directly to minio for listing, upload, and download operations.  You can even continue to use `minio/mc` or `boto3` , with some caveats.
* Permissions-aware indexing and aggregation across the system.
* Hub-and-spoke architecture.  Run a MinIO node wherever you have data, and it will be available through Workspaces.  Even **regular users** can introduce new nodes into the system and retain full control of their data.

## Screenshots

![Images in a directory](docs/images/screen-images.png)

![directory of directories](docs/images/screen-dirs.png)

``` bash
# List user workspaces
~$ wio workspace ls
[2020-10-17T21:07:18.996866] admin@subdavis.com/meva/ (unmanaged)
[2020-10-17T21:06:11.048850] admin@subdavis.com/second/ (private)
[2020-10-17T21:06:11.470730] admin@subdavis.com/third/ (private)
[2020-10-17T21:07:18.188769] admin@subdavis.com/kobodls/ (unmanaged)
[2020-10-17T21:07:18.720848] admin@subdavis.com/metabolomics/ (unmanaged)
[2020-10-17T21:06:10.623132] admin@subdavis.com/first/ (public)
[2020-10-17T21:07:17.911934] dmin@subdavis.com/_samples/ (unmanaged)
[2020-10-17T21:07:19.575340] admin@subdavis.com/viame-web/ (unmanaged)

# List instances of MinIO
~$ wio node ls
[2020-10-17T21:06:08.480801] ddb915fb-d911-4a8a-8971-b2fccd4e4ea8 http://hostname:9000 default
[2020-10-17T21:06:09.803527] 6a4cf079-6c2f-4f09-abb0-abe39379e168 http://hostname:9100 secondary

# List contens of workspace using MinIO client
~$ wio mc ls viame-web/NOAAWorkshop2020/
[2020-10-18 17:47:33 EDT]      0B Aerial Footage/
[2020-10-18 17:47:33 EDT]      0B Completed Pipelines/
[2020-10-18 17:47:33 EDT]      0B Fish Test Set/
[2020-10-18 17:47:33 EDT]      0B Fish Training/
[2020-10-18 17:47:33 EDT]      0B Scallop Test Set/
[2020-10-18 17:47:33 EDT]      0B Sea Lion Test Set/
[2020-10-18 17:47:33 EDT]      0B Sea Lion Training/
```

## Philosophy

Data management should come to users and the places they already have data.  If your team wants to use powerful industry-standard tools like MinIO and ElasticSearch, but needs permissions management, WorkspacesIO might be an option.

## Caveats

For whatever reason, [you can't explicitly revoke STS credentials](https://stackoverflow.com/questions/47026661/explicitly-expire-tokens-acquired-from-aws-security-token-service).  That's how AWS does it so MinIO won't implement it either.  This means that share revocation has a big asterisk: anyone with outstanding credentials can continue to modify data in s3 until that share expires.

## FAQ

> What's a workspace?

It's just a folder.  Users manage the heirarchy within.  Permissions are managed at the workspace level.  You can search for workspace contents and share individual objects, but these are features of elasticsearch and minio, respectively.

> Who is this for?

WorkspacesIO is for organizations that need to manage large quantities of slow-moving data of the sort that laboratories and research teams accumulate.  Think Samba, CIFS, FTP, SSHFS.  WorksapcesIO can map your existing data while you transition, or run side-by-side forever.

> What if I want to share a single file?

There's always pre-signed URLs to email a collegue.  But you shouldn't think of this like Google Drive; WorkspacesIO isn't for slide decks.

> Why not just MinIO?

MinIO's multi-user management is great when all users a) need their own space or b) can share everything, but it's cumbersome for dynamic permissions management.  WorkspacesIO gives you Role-based access control.

> Can I just try it?  What if I hate it?

Because it doesn't modify the structure of your data on disk, WorkspacesIO is easy to try.

> Multiple nodes?  Isn't that just MinIO Distributed Mode?

Not at all.  MinIO's Distributed Mode solves an operational and deeply technical problem.  It allows for data redundancy and high availability.  WorkspacesIO solves a bureaucratic problem.  You've got data on different servers and workstations in different locations.  You can't reasonably migrate it all into the same storage cluster, but you want to provide read/write/search to certain authenticated users across your org.

## Development setup

### Server

Install the [ldc](https://github.com/Kitware/ldc) tool.

``` sh
# run production services
ldc up

# swap in the development container
ldc dev workspaces
```

Now you're running a fastapi service in development mode inside a docker container. Local directories are mounted in. 

### Client

``` sh
virtualenv -p python3 venv/
venv/bin/activate

pip3 install -e .
pip3 install -r dev.requirements.txt

wio --help
```

### Referring to workspaces

You can refer to workspaces either

* directly by `workspacename/`
* through their owner by `owner/workspacename/`

# Credit

Credit to [Filestash.app](https://github.com/mickael-kerjean/filestash) for the frontend file browser. Integration into workspacesio is ongong and can be found at [subdavis/filestash](https://github.com/subdavis/filestash)
