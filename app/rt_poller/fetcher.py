import requests

from app.common.feeds import FeedConfig


def fetch_vehicle_positions(feed: FeedConfig, timeout: int = 30) -> bytes:
    """Fetch VehiclePositions.pb feed."""
    response = requests.get(feed.vehicle_positions_url, timeout=timeout)
    response.raise_for_status()
    return response.content


def fetch_trip_updates(feed: FeedConfig, timeout: int = 30) -> bytes:
    """Fetch TripUpdates.pb feed."""
    response = requests.get(feed.trip_updates_url, timeout=timeout)
    response.raise_for_status()
    return response.content
