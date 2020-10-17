# Design

This document will explore some of the design choices that went into WorkspacesIO.

## Goal

WorkspacesIO provides intuitive object storage, indexing, artifact generation, and data lifecycle management using the very best open source tooling available given the constraints of role-based access control.  When possible, WorkspacesIO should provide thin wrapping around existing tools or defer completely in order to provide more power to users.

## Risk

WorkspacesIO does not protect consumers from the API surfaces of its composite stack, MinIO and ElasticSearch in particular.  Significant changes in the feature offerings of these tools could cause instability for  WorkspacesIO users.  Through this added power, users are also less protected.

## Alternatives

Some off-the-shelf data storage solutions would be better for sync/search, but provide poor experience for highly technical end users.  No decent command line options, inability to map over existing data volumes.

* NextCloud
* Seafile
* Pydio Cells

Other frameworks for managing digital collections provide too little, requiring a large up-front investment and code in order to even determine if the capabilitis meet your needs.

* https://github.com/inveniosoftware/invenio

Everything else is over-specialized.

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
