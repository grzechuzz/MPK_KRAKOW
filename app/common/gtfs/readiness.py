import logging
import time

from app.common.redis.connection import get_client

REDIS_KEY_GTFS_READY = "gtfs:ready"

logger = logging.getLogger(__name__)


def wait_for_gtfs_ready(timeout: int = 180, poll_interval: int = 5) -> None:
    """Block until GTFS data is ready."""
    logger.info("Waiting for GTFS ready...")
    redis = get_client()
    start = time.time()

    while time.time() - start < timeout:
        if redis.exists(REDIS_KEY_GTFS_READY):
            logger.info("GTFS data ready")
            return
        time.sleep(poll_interval)

    raise TimeoutError(f"GTFS not ready after {timeout}s")
