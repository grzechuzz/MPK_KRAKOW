import requests

from app.collector.collector.settings import VP_URL


class FetchError(RuntimeError):
    pass


def fetch_vehicle_positions_pb(timeout_seconds: int = 20) -> bytes:
    try:
        r = requests.get(VP_URL, timeout=timeout_seconds)
        r.raise_for_status()
        return r.content
    except requests.exceptions.RequestException as e:
        raise FetchError(f"Failed to fetch VehiclePositions from {VP_URL!r}: {e}") from e
