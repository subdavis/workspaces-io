"""
Helper functions for working with S3 and STS
"""
import base64
import datetime
import hashlib
import hmac
import os
import posixpath
import sys
import uuid
from typing import List, Optional, Set, Tuple, TypedDict, Union

from . import models, schemas, settings


def sanitize(name: str) -> str:
    # TODO
    return name


def getWorkspaceKey(
    workspace: Union[models.Workspace, schemas.WorkspaceDB],
    root: Optional[Union[models.WorkspaceRoot, schemas.WorkspaceRootDB, None]] = None,
) -> str:
    """
    Determine full object prefix for a given workspace
    """
    root_base_path = root.base_path if root else workspace.root.base_path
    inner_path = posixpath.join(workspace.owner.username, sanitize(workspace.name))
    if workspace.base_path != None:
        inner_path = workspace.base_path
    return posixpath.join(
        root_base_path,
        inner_path,
    ).strip("/")


def makeRoleSessionName(
    user: schemas.UserBase, workspace: Optional[models.Workspace]
) -> str:
    return f"{user.id}::{workspace}"


PolicyDoc = TypedDict(
    "PolicyDoc",
    {
        "Version": str,
        "Statement": List[dict],
    },
)


def makePolicy(
    user: schemas.UserBase,
    workspaces: List[models.Workspace],
    foreign_workspaces: List[Tuple[models.Workspace, Optional[models.Share]]],
) -> PolicyDoc:
    """
    Make a policy for the given user to access s3 based on
    https://aws.amazon.com/premiumsupport/knowledge-center/s3-folder-user-access/

    All workspaces passed in MUST be part of the same storage node.

    :param user: the policyholder
    :param workspaces: only add these to policy if they're public or owned by user
    :param foregin_workspaces: add these according to their shares
    """
    if len(workspaces) == 0 and len(foreign_workspaces) == 0:
        raise ValueError("No workspaces found")

    # Some sets to prevent duplicate policies from being added
    # such as if two different public workspaces come from the same root
    node_id: Union[uuid.UUID, None] = None
    root_ids: Set[uuid.UUID] = set()
    workspace_ids: Set[uuid.UUID] = set()
    statements: List[dict] = []
    for w in workspaces:
        if node_id is not None and w.root.storage_node.id != node_id:
            raise ValueError("Multiple nodes found in workspace list")
        elif node_id is None:
            node_id = w.root.storage_node.id
        if w.root_id in root_ids:
            continue
        root_ids.add(w.root_id)
        bucket = w.root.bucket
        resourceBase = f"arn:aws:s3:::{bucket}"
        basepath = w.root.base_path or ""
        workspacekey = getWorkspaceKey(w)
        usernamekey = workspacekey.rstrip(w.name)

        statements.append(
            # enables getting region info from bucket
            {
                "Action": "s3:GetBucketLocation",
                "Effect": "Allow",
                "Resource": resourceBase,
            }
        )

        if w.root.root_type == schemas.RootType.PUBLIC:
            statements += [
                # enables listing all public bucket contents
                {
                    "Action": ["s3:ListBucket"],
                    "Effect": "Allow",
                    "Resource": resourceBase,
                    "Condition": {
                        "StringLike": {
                            "s3:prefix": posixpath.join(basepath, "*"),
                            "s3:delimiter": "/",
                        }
                    },
                },
                # enables fetching all public bucket contents
                {
                    "Effect": "Allow",
                    "Action": ["s3:GetObject"],
                    "Resource": posixpath.join(resourceBase, basepath, "*"),
                },
            ]
            if w.owner_id == user.id:
                # enables update and delete of owned bucket contents
                statements.append(
                    {
                        "Effect": "Allow",
                        "Action": ["s3:*"],
                        "Resource": [
                            posixpath.join(resourceBase, basepath, usernamekey, "*")
                        ],
                    }
                )
        elif w.root.root_type == schemas.RootType.PRIVATE:
            statements += [
                # enables listing all owned private buckets
                {
                    "Action": ["s3:ListBucket"],
                    "Effect": "Allow",
                    "Resource": resourceBase,
                    "Condition": {
                        "StringLike": {
                            "s3:prefix": posixpath.join(basepath, usernamekey, "*"),
                            "s3:delimiter": "/",
                        }
                    },
                },
                # enables get, update, delete of all private owned buckets
                {
                    "Effect": "Allow",
                    "Action": ["s3:*"],
                    "Resource": posixpath.join(
                        resourceBase, basepath, usernamekey, "*"
                    ),
                },
            ]
    for w, share in foreign_workspaces:
        if node_id is not None and w.root.storage_node.id != node_id:
            raise ValueError("Multiple nodes found in workspace list")
        elif node_id is None:
            node_id = w.root.storage_node.id
        bucket = w.root.bucket
        resourceBase = f"arn:aws:s3:::{bucket}"
        workspacekey = getWorkspaceKey(w)
        statements += [
            {
                "Action": ["s3:ListBucket"],
                "Effect": "Allow",
                "Resource": [resourceBase],
                "Condition": {
                    "StringLike": {"s3:prefix": workspacekey, "s3:delimiter": "/"}
                },
            },
            {
                "Action": ["s3:ListBucket"],
                "Effect": "Allow",
                "Resource": [resourceBase],
                "Condition": {
                    "StringLike": {"s3:prefix": posixpath.join(workspacekey, "*")}
                },
            },
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject"],
                "Resource": [posixpath.join(resourceBase, workspacekey, "*")],
            },
        ]
        if share is not None:
            if (
                share.permission is schemas.ShareType.READWRITE
                or share.permission is schemas.ShareType.OWN
            ):
                statements.append(
                    {
                        "Effect": "Allow",
                        "Action": ["s3:PutObject", "s3:DeleteObject"],
                        "Resource": [posixpath.join(resourceBase, workspacekey, "*")],
                    }
                )
        if share is None and w.owner_id == user.id:
            statements.append(
                {
                    "Effect": "Allow",
                    "Action": ["s3:PutObject", "s3:DeleteObject"],
                    "Resource": [posixpath.join(resourceBase, workspacekey, "*")],
                }
            )

    return {
        "Version": "2012-10-17",
        "Statement": statements,
    }


def makeEmptyPolicy():
    return {
        "Version": "2012-10-17",
        "Statement": [],
    }


S3V4Headers = TypedDict(
    "S3V4Headers",
    {
        "x-amz-date": str,
        "Authorization": str,
    },
)


def get_s3v4_headers(
    access_key: str,
    secret_key: str,
    region="us-east-1",
    service="s3",
    host="localhost:9000",
    endpoint="http://localhost:9000",
    uri="/",
    request_parameters="",
) -> S3V4Headers:
    method = "GET"
    # Key derivation functions. See:
    # http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
    def sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def getSignatureKey(key, dateStamp, regionName, serviceName):
        kDate = sign(("AWS4" + key).encode("utf-8"), dateStamp)
        kRegion = sign(kDate, regionName)
        kService = sign(kRegion, serviceName)
        kSigning = sign(kService, "aws4_request")
        return kSigning

    # Create a date for headers and the credential string
    t = datetime.datetime.utcnow()
    amzdate = t.strftime("%Y%m%dT%H%M%SZ")
    datestamp = t.strftime("%Y%m%d")  # Date w/o time, used in credential scope

    # ************* TASK 1: CREATE A CANONICAL REQUEST *************
    # http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html

    # Step 1 is to define the verb (GET, POST, etc.)--already done.

    # Step 2: Create canonical URI--the part of the URI from domain to query
    # string (use '/' if no path)
    canonical_uri = uri

    # Step 3: Create the canonical query string. In this example (a GET request),
    # request parameters are in the query string. Query string values must
    # be URL-encoded (space=%20). The parameters must be sorted by name.
    # For this example, the query string is pre-formatted in the request_parameters variable.
    canonical_querystring = request_parameters

    # Step 4: Create the canonical headers and signed headers. Header names
    # must be trimmed and lowercase, and sorted in code point order from
    # low to high. Note that there is a trailing \n.
    canonical_headers = "host:" + host + "\n" + "x-amz-date:" + amzdate + "\n"

    # Step 5: Create the list of signed headers. This lists the headers
    # in the canonical_headers list, delimited with ";" and in alpha order.
    # Note: The request can include any headers; canonical_headers and
    # signed_headers lists those that you want to be included in the
    # hash of the request. "Host" and "x-amz-date" are always required.
    signed_headers = "host;x-amz-date"

    # Step 6: Create payload hash (hash of the request body content). For GET
    # requests, the payload is an empty string ("").
    payload_hash = hashlib.sha256(("").encode("utf-8")).hexdigest()

    # Step 7: Combine elements to create canonical request
    canonical_request = (
        method
        + "\n"
        + canonical_uri
        + "\n"
        + canonical_querystring
        + "\n"
        + canonical_headers
        + "\n"
        + signed_headers
        + "\n"
        + payload_hash
    )

    # ************* TASK 2: CREATE THE STRING TO SIGN*************
    # Match the algorithm to the hashing algorithm you use, either SHA-1 or
    # SHA-256 (recommended)
    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = datestamp + "/" + region + "/" + service + "/" + "aws4_request"
    string_to_sign = (
        algorithm
        + "\n"
        + amzdate
        + "\n"
        + credential_scope
        + "\n"
        + hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    )

    # ************* TASK 3: CALCULATE THE SIGNATURE *************
    # Create the signing key using the function defined above.
    signing_key = getSignatureKey(secret_key, datestamp, region, service)

    # Sign the string_to_sign using the signing_key
    signature = hmac.new(
        signing_key, (string_to_sign).encode("utf-8"), hashlib.sha256
    ).hexdigest()

    # ************* TASK 4: ADD SIGNING INFORMATION TO THE REQUEST *************
    # The signing information can be either in a query string value or in
    # a header named Authorization. This code shows how to use a header.
    # Create authorization header and add to request headers
    authorization_header = (
        algorithm
        + " "
        + "Credential="
        + access_key
        + "/"
        + credential_scope
        + ", "
        + "SignedHeaders="
        + signed_headers
        + ", "
        + "Signature="
        + signature
    )

    # The request can include any headers, but MUST include "host", "x-amz-date",
    # and (for this scenario) "Authorization". "host" and "x-amz-date" must
    # be included in the canonical_headers and signed_headers, as noted
    # earlier. Order here is not significant.
    # Python note: The 'host' header is added automatically by the Python 'requests' library.
    headers: S3V4Headers = {
        "x-amz-date": amzdate,
        "Authorization": authorization_header,
    }
    return headers
