import urllib.parse
from typing import Dict


def build_url(base_url: str, path: str = "", args_dict: Dict[str, str] = {}) -> str:
    # Returns a list in the structure of urlparse.ParseResult
    url_parts = list(urllib.parse.urlparse(base_url))
    url_parts[2] = path
    url_parts[4] = urllib.parse.urlencode(args_dict)
    return urllib.parse.urlunparse(url_parts)
