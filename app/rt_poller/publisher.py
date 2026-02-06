import json
import logging

import redis

from app.common.db.connection import get_session
from app.common.db.repositories.gtfs_static import GtfsStaticRepository
from app.common.feeds import FeedConfig
from app.common.gtfs.parser import parse_trip_updates, parse_vehicle_positions
from app.common.redis.repositories.trip_updates import TripUpdatesRepository

logger = logging.getLogger(__name__)

VEHICLE_POSITIONS_CHANNEL = "vehicle_positions"
MAX_CACHE_SIZE = 5000


class Publisher:
    """Publishes parsed GTFS RT data to Redis Pub/Sub."""

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client
        self._trip_updates_repository = TripUpdatesRepository(redis_client)
        self._stop_id_to_seq_cache: dict[str, dict[str, int]] = {}

    def publish_vehicle_positions(self, feed: FeedConfig, pb_data: bytes) -> int:
        """
        Parse and publish vehicle positions to Redis Pub/Sub. Returns number of positions published.
        """
        positions = parse_vehicle_positions(pb_data, feed.agency)

        for pos in positions:
            message = {
                "agency": pos.agency.value,
                "trip_id": pos.trip_id,
                "vehicle_id": pos.vehicle_id,
                "license_plate": pos.license_plate,
                "stop_id": pos.stop_id,
                "stop_sequence": pos.stop_sequence,
                "status": pos.status.value if pos.status else None,
                "timestamp": pos.timestamp.isoformat(),
            }
            self._redis.publish(VEHICLE_POSITIONS_CHANNEL, json.dumps(message))

        return len(positions)

    def process_trip_updates(self, feed: FeedConfig, pb_data: bytes) -> int:
        """
        Parse and cache trip updates in Redis. Returns number of trip updates processed.
        """
        updates = parse_trip_updates(pb_data, feed.agency)

        with get_session() as session:
            static_repo = GtfsStaticRepository(session)

            for update in updates:
                stop_id_to_seq = self._get_stop_id_to_seq(static_repo, update.trip_id)
                self._trip_updates_repository.update(update, stop_id_to_seq)

        return len(updates)

    def _get_stop_id_to_seq(self, repo: GtfsStaticRepository, trip_id: str) -> dict[str, int]:
        """Get stop_id to stop_sequence mapping with caching."""
        if trip_id not in self._stop_id_to_seq_cache:
            self._stop_id_to_seq_cache[trip_id] = repo.build_stop_id_to_sequence_map(trip_id)

            if len(self._stop_id_to_seq_cache) > MAX_CACHE_SIZE:
                self._stop_id_to_seq_cache.clear()
                self._stop_id_to_seq_cache[trip_id] = repo.build_stop_id_to_sequence_map(trip_id)

        return self._stop_id_to_seq_cache[trip_id]
