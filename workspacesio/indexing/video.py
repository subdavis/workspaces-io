import posixpath
import urllib.parse

import ffmpeg

from workspacesio import s3utils, schemas

from . import schemas as indexing_schemas


def probe(
    doc: indexing_schemas.IndexDocumentBase,
    node: schemas.StorageNodeOperator,
    root: schemas.WorkspaceRootDB,
    workspace: schemas.WorkspaceDB,
):
    endpoint = node.api_url
    parsed = urllib.parse.urlparse(endpoint)
    host = parsed.netloc
    headerstring = ""
    uri = posixpath.join(
        "/",
        root.bucket,
        s3utils.getWorkspaceKey(workspace, root),
        doc.path.lstrip("/"),
    )
    headers = s3utils.get_s3v4_headers(
        access_key=node.access_key_id,
        secret_key=node.secret_access_key,
        region=node.region_name,
        host=host,
        endpoint=endpoint,
        uri=uri,
    )
    headerstring = "\r\n".join([f"{key}:{val}" for key, val in headers.items()])
    url = urllib.parse.urljoin(endpoint, uri)
    try:
        data = ffmpeg.probe(url, headers=headerstring)
        if len(data["streams"]):
            streams = data["streams"][0]
            doc.codec_tag_string = streams["codec_tag_string"]
            doc.r_frame_rate = streams["r_frame_rate"]
            doc.width = streams["width"]
            doc.height = streams["height"]
            doc.duration_ts = streams["duration_ts"]
            try:
                doc.bit_rate = int(streams["bit_rate"])
            except:
                doc.bit_rate = streams["bit_rate"]
        doc.duration_sec = data["format"]["duration"]
        doc.format_name = data["format"]["format_name"]
    except ffmpeg._run.Error as e:
        raise indexing_schemas.ProducerError(e)
