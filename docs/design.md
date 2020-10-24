# Design

This document will explore some of the design choices that went into WorkspacesIO.

## Goal

WorkspacesIO provides intuitive object storage, indexing, artifact generation, and data lifecycle management using the very best open source tooling available given the constraints of role-based access control.  When possible, WorkspacesIO should provide thin wrapping around existing tools or defer completely in order to provide more power to users.

## Code Quality and Maintainability

These are the guiding values of WorkspacesIO.

* Use modern, typeful python style that any python developer could understand.
* Use excellent linting and testing practices to catch problems early.
* Keep your footprint small, and defer as much complex functionality to MinIO/ElasticSearc/Filestash as possible.

## Risk

WorkspacesIO does not protect consumers from the API surfaces of its composite stack, MinIO and ElasticSearch in particular.  Significant changes in the feature offerings of these tools could cause instability for  WorkspacesIO users.  Through this added power, users are also less protected.

Users should consider this a feature.  MinIO and Elastic Co have shown themselves to be more technically competent, more user-focused, and better stuards of open-source than the companies behind any of the alternatives below.

## Data Storage Alternatives

Some off-the-shelf data storage solutions would be better for sync/search, but provide poor experience for highly technical end users.  No decent command line options, inability to map over existing data volumes, and comparably poor performance are some major issues we want to address.

* NextCloud
* Seafile
* Pydio Cells

Everything else is over-specialized.

## Indexing Alternatives

WorkspacesIO does not seek to compete with indexing tools like those listed below. These tools are great at indexing documents, but they are **destructive**.  They insist on owning the documents they index rather than mapping over existing file structures, making them unsuitable for many users.  Only Mayan provides access control.

* [Mayan EDMS](https://docs.mayan-edms.com/)
* [Paperless](https://github.com/the-paperless-project/paperless)
* [Lodestone](https://github.com/LodestoneHQ/lodestone)

WorkspacesIO will provide some degree of full text search, hopefully comparable to what seafile provides, but it is not an EDMS.

## Stack

Each component of the stack was chosen for its history and stability among other open source offerings.  This stack is intended to mitigate above noted risk.

* ElasticSearch is peerless.
* MinIO provides exceptional value to end users by making WorkspacesIO instantly compatible with tons of existing S3 tooling.
* OpenID Connect via KeyCloak and Auth0 provides flexibility for integration in existing auth realms.
* Postgres + SQLAlchemy provides a typed ORM with excellent community support.

Minimal frontend uses a more experimental stack that promises to be easy to understand for contributors and sustainable for many years.

* TypeScript
* Vue 3
* Vite
* Tailwind CSS
