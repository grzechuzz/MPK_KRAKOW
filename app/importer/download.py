import tempfile
from pathlib import Path

import requests

from app.common.constants import (
    IMPORT_FETCH_RETRY_ATTEMPTS,
    IMPORT_FETCH_RETRY_BACKOFF_SECONDS,
    IMPORT_FETCH_TIMEOUT_SECONDS,
    USER_AGENT,
)
from app.common.feeds import FeedConfig
from app.common.retry import retry_sync

_HEADERS = {"User-Agent": USER_AGENT}


def download_gtfs_zip(feed: FeedConfig, timeout: int = IMPORT_FETCH_TIMEOUT_SECONDS) -> Path:
    """
    Download GTFS Static ZIP to temporary file. Returns path to downloaded ZIP.
    """
    response = retry_sync(
        lambda: requests.get(feed.static_url, timeout=timeout, headers=_HEADERS),
        attempts=IMPORT_FETCH_RETRY_ATTEMPTS,
        backoff_seconds=IMPORT_FETCH_RETRY_BACKOFF_SECONDS,
        retriable_exceptions=(requests.RequestException,),
    )
    response.raise_for_status()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    temp_file.write(response.content)
    temp_file.close()

    return Path(temp_file.name)
