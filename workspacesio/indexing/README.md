# Indexing

Indexes are maintained in 2 ways

* manual crawl using command line
* ongoing maintenance using bucket notifications

## concepts

The main index is a single elasticsearch index with exactly 1 record for each object in each index-enabled workspace.

Indexing must be run on an entire workspace before it can be re-started.  In other words, you can't update one part of a workspace more frequently than another.  If you need this, you should break out into another workspace.

A new index DB record is created for each complete run.  Bucket notifications that trigger index updates are always attributed to the most recent ongoing or complete index.

Indexes can be in an ongoing, complete, or failed state.

ES index records follow upsert-delete.  To keep the index current, at the end of a round of indexing, the only remaining step is to drop all records that weren't updated during the last completed index.  Even if manual and bucket-noficiation-based indexing happens concurrently, this will prevent data loss and duplication.

## limitations

Indexing can track objects when they are created, delted, moved, and copied through bucket notifications, which are provided when manipulation happens through an S3 interface.

When disk operations mutate data, all moves and delete operations will appear as deletes.  All copy and move operations will appear as new objects.  More robust change tracking is currently out of scope for workspacesio.

When audit history matters, s3 gateway must be used.
