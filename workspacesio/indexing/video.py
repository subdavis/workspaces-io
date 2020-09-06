import ffmpeg

from . import schemas as indexing_schemas


def extract_metadata(doc: indexing_schemas.IndexDocumentBase, path: str):
    print(ffmpeg.probe(path))
