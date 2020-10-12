import urllib

from typing import Dict, Optional


def build_url(base_url, path: Optional[str] = None, args_dict: Dict[str, str] = {}):
    # Returns a list in the structure of urlparse.ParseResult
    url_parts = list(urllib.parse.urlparse(base_url))
    if path is not None:
        url_parts[2] = path
    url_parts[4] = urllib.parse.urlencode(args_dict)
    return urllib.parse.urlunparse(url_parts)
