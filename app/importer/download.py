import tempfile
from pathlib import Path

import requests

from app.common.feeds import FeedConfig


def download_gtfs_zip(feed: FeedConfig, timeout: int = 60) -> Path:
    """
    Download GTFS Static ZIP to temporary file. Returns path to downloaded ZIP.
    """
    response = requests.get(feed.static_url, timeout=timeout)
    response.raise_for_status()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    temp_file.write(response.content)
    temp_file.close()

    return Path(temp_file.name)
