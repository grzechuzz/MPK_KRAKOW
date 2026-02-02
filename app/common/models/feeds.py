from dataclasses import dataclass

from app.common.models.enums import Agency


@dataclass(frozen=True)
class FeedConfig:
    """Configuration for a single GTFS feed (static + realtime)"""

    agency: Agency
    static_url: str
    static_filename: str
    vehicle_positions_url: str
    trip_updates_url: str


FEED_CONFIGS: dict[Agency, FeedConfig] = {
    Agency.MPK: FeedConfig(
        agency=Agency.MPK,
        static_url="https://gtfs.ztp.krakow.pl/GTFS_KRK_A.zip",
        static_filename="GTFS_KRK_A.zip",
        vehicle_positions_url="https://gtfs.ztp.krakow.pl/VehiclePositions_A.pb",
        trip_updates_url="https://gtfs.ztp.krakow.pl/TripUpdates_A.pb",
    ),
    Agency.MOBILIS: FeedConfig(
        agency=Agency.MOBILIS,
        static_url="https://gtfs.ztp.krakow.pl/GTFS_KRK_M.zip",
        static_filename="GTFS_KRK_M.zip",
        vehicle_positions_url="https://gtfs.ztp.krakow.pl/VehiclePositions_M.pb",
        trip_updates_url="https://gtfs.ztp.krakow.pl/TripUpdates_M.pb",
    )
}


def get_feed_config(agency: Agency) -> FeedConfig:
    return FEED_CONFIGS[agency]


def get_all_feed_configs() -> list[FeedConfig]:
    return list(FEED_CONFIGS.values())
