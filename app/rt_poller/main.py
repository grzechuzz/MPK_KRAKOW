import logging
import time

from app.common.feeds import get_all_feed_configs
from app.common.gtfs.readiness import wait_for_gtfs_ready
from app.common.redis.connection import get_client
from app.rt_poller.fetcher import fetch_trip_updates, fetch_vehicle_positions
from app.rt_poller.publisher import Publisher

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 3


def run_poller() -> None:
    """Run the GTFS Realtime poller loop"""
    redis = get_client()
    publisher = Publisher(redis)
    feeds = get_all_feed_configs()

    logger.info(f"Starting poller for {len(feeds)} feeds")

    while True:
        for feed in feeds:
            try:
                vp_data = fetch_vehicle_positions(feed)
                vp_count = publisher.publish_vehicle_positions(feed, vp_data)
                logger.debug(f"{feed.agency.value}: Published {vp_count} vehicle positions")

                tu_data = fetch_trip_updates(feed)
                tu_count = publisher.process_trip_updates(feed, tu_data)
                logger.debug(f"{feed.agency.value}: Cached {tu_count} trip updates")

            except Exception as e:
                logger.exception(f"Error polling {feed.agency.value}: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)


def main() -> None:
    logger.info("GTFS Realtime poller starting, waiting for GTFS Static data...")
    wait_for_gtfs_ready()
    logger.info("Starting poller")
    run_poller()


if __name__ == "__main__":
    main()
