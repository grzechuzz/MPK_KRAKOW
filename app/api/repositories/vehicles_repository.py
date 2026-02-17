import logging

import requests

from app.common.constants import PB_MIN_PAYLOAD_BYTES, USER_AGENT
from app.common.feeds import get_all_feed_configs
from app.common.gtfs.parser import parse_vehicle_positions
from app.common.models.gtfs_realtime import VehiclePosition

logger = logging.getLogger(__name__)


class VehiclesRepository:
    """Fetches live vehicle positions from GTFS Realtime feeds."""

    def fetch_all_positions(self) -> list[VehiclePosition]:
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
