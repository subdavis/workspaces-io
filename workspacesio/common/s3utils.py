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
import urllib.parse
import uuid
from typing import List, Optional, Set, Tuple, TypedDict, Union

import boto3
import minio
from botocore.client import Config

from . import schemas


class Boto3ClientCache:
    """
    There may be many s3 nodes in the cluser.  Once a client has been established,
    cache it for future use.  This class works for sts and s3 type clients.
    """

    def __init__(self):
        self.cache: Dict[str, boto3.Session] = {}

    @staticmethod
    def _get_primary_key(client_type: str, node: schemas.StorageNodeOperator) -> str:
        if not client_type in ["s3", "sts"]:
            raise ValueError(f"{client_type} unsupported by cache")
        primary_key = (
            (
                f"{client_type}{node.region_name}{node.api_url}"
                f"{node.access_key_id}{node.secret_access_key}"
            )
            .lower()
            .encode("utf-8")
        )
        return hashlib.sha256(primary_key).hexdigest()

    def get_client(
        self,
        client_type: str,
        node: schemas.StorageNodeOperator,
    ) -> boto3.Session:
        primary_key_short_sha256 = Boto3ClientCache._get_primary_key(client_type, node)
        client = self.cache.get(primary_key_short_sha256, None)
        if client is None:
            config = Config()
            if client_type == "s3":
                config = Config(signature_version="s3v4")
                client = boto3.client(
                    client_type,
                    region_name=node.region_name,
                    endpoint_url=node.api_url,
                    aws_access_key_id=node.access_key_id,
                    aws_secret_access_key=node.secret_access_key,
                    config=config,
                )
            elif client_type == "sts":
                is_aws = node.assume_role_arn is not None
                api_url = node.api_url
                if node.sts_api_url:
                    api_url = node.sts_api_url
                elif is_aws:
                    api_url = f"https://sts.{node.region_name}.amazonaws.com"
                client = boto3.client(
                    client_type,
                    region_name=node.region_name,
                    endpoint_url=api_url,
                    aws_access_key_id=node.access_key_id,
                    aws_secret_access_key=node.secret_access_key,
                )
            else:
                raise NotImplementedError("Client type not implemented")
            self.cache[primary_key_short_sha256] = client
        return client

    def get_minio_sdk_client(self, node: schemas.StorageNodeOperator) -> minio.Minio:
        primary_key_short_sha256 = (
            Boto3ClientCache._get_primary_key("s3", node) + "minio"
        )
        client = self.cache.get(primary_key_short_sha256, None)
        url = urllib.parse.urlparse(node.api_url)
        if client is None:
            client = minio.Minio(
                url.netloc,
                access_key=node.access_key_id,
                secret_key=node.secret_access_key,
                secure=False,
            )
            self.cache[primary_key_short_sha256] = client
        return client


def sanitize(name: str) -> str:
    # TODO
    return name


def getWorkspaceKey(
    workspace: schemas.WorkspaceDB,
    root: Optional[schemas.WorkspaceRootDB] = None,
) -> str:
    """
    Determine full object prefix for a given workspace
    """
    root_base_path = root.base_path if root else workspace.root.base_path
    inner_path = posixpath.join(workspace.owner.username, sanitize(workspace.name))
    if workspace.base_path != None:
        inner_path = str(workspace.base_path)
    return posixpath.join(
        root_base_path,
        inner_path,
    ).strip("/")


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
