# Artifacts

Mostly for thumbnails, transcoding, etc.

Artifacts are generated during manual indexing/crawling, and in an ongoing fashion through bucket notifications.

Artifact lifecycle is bound to index document lifecycle.  See indexing/README.md for more.

## Manual crawl

During a manual index, logic for artifact generation looks like this:

``` text
for object in workspace:
  if object should generate artifact:
    if artifacts not already in minio:
      generate new artifacts
      place in minio
      create artifact record in workspsaces server
    else:
      get artifact record from workspaces server
      if artifact's version modification time and size do not match object.
        generate new artifacts
        place in minio
        update artifact record in workspaces server
```

## Bucket notification

Same as above, but without the for loop

## Artifact policy

Future work.  Workspaces now will all have the same policy.  For example, if every video should have a thumbnail from frame 5, that can't change per workspace.

In the future, I'd like to have some kind of workspace-level policy document describing the types of artifacts that a workspace's objects require.

For now, this will be controlled with command-line arguments.

Policy could be based on:

* content type
* size
* last update time
* Name regex
* index tags

Policy could determine:

* which artifacts are generated
* specific parameters to generator functions
