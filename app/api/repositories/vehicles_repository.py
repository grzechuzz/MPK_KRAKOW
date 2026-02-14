import logging

import requests

from app.common.constants import PB_MIN_PAYLOAD_BYTES, USER_AGENT
from app.common.db.connection import get_session
from app.common.db.repositories.gtfs_static import GtfsStaticRepository
from app.common.feeds import get_all_feed_configs
from app.common.gtfs.parser import parse_vehicle_positions
from app.common.models.gtfs_realtime import VehiclePosition

logger = logging.getLogger(__name__)


def load_trip_info() -> dict[str, tuple[str, str]]:
    """Load trip_id -> (line_number, headsign) via GtfsStaticRepository."""
    with get_session() as session:
        return GtfsStaticRepository(session).get_all_trip_info()


def fetch_all_positions() -> list[VehiclePosition]:
    """Fetch and parse vehicle positions from GTFS Realtime feeds."""
    all_positions: list[VehiclePosition] = []

    for feed in get_all_feed_configs():
        try:
            resp = requests.get(feed.vehicle_positions_url, timeout=10, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            if len(resp.content) < PB_MIN_PAYLOAD_BYTES:
                continue
            positions = parse_vehicle_positions(resp.content, feed.agency)
            all_positions.extend(positions)
        except Exception:
            logger.warning(f"Failed to fetch positions for {feed.agency.value}", exc_info=True)

    return all_positions
