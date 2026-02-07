import json
import logging
from collections.abc import Iterator
from datetime import datetime

import redis

from app.common.models.enums import Agency, VehicleStatus
from app.common.models.gtfs_realtime import VehiclePosition

logger = logging.getLogger(__name__)

VEHICLE_POSITIONS_CHANNEL = "vehicle_positions"


class Subscriber:
    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client
        self._pubsub = redis_client.pubsub()  # type: ignore[no-untyped-call]
        self._pubsub.subscribe(VEHICLE_POSITIONS_CHANNEL)

    def listen(self) -> Iterator[VehiclePosition]:
        """
        Listen for vehicle position messages and yields VehicleUpdate for each message.
        """
        for message in self._pubsub.listen():
            if message["type"] != "message":
                continue

            try:
                data = json.loads(message["data"])
                yield VehiclePosition(
                    agency=Agency(data["agency"]),
                    trip_id=data["trip_id"],
                    vehicle_id=data["vehicle_id"],
                    license_plate=data["license_plate"],
                    latitude=None,
                    longitude=None,
                    bearing=None,
                    stop_id=data["stop_id"],
                    stop_sequence=data["stop_sequence"],
                    status=VehicleStatus(data["status"]) if data["status"] else None,
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                )
            except Exception as e:
                logger.exception(f"Failed to parse message: {e}")
                continue

    def close(self) -> None:
        self._pubsub.close()
