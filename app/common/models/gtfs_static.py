from dataclasses import dataclass


@dataclass(frozen=True)
class Agency:
    """Transit agency from agency.txt."""

    agency_id: str
    agency_name: str


@dataclass(frozen=True)
class Route:
    """Transit route from routes.txt."""

    route_id: str
    agency_id: str
    route_short_name: str  # Line number (e.g. "304", "503")


@dataclass(frozen=True)
class Stop:
    """Transit stop from stops.txt."""

    stop_id: str
    stop_name: str
    stop_code: str | None
    stop_desc: str | None  # Combined with stop_name forms the full description like "Rondo Grunwaldzkie 06"
    stop_lat: float | None
    stop_lon: float | None


@dataclass(frozen=True)
class Trip:
    """Transit trip from trips.txt."""

    trip_id: str
    route_id: str
    service_id: str
    direction_id: int | None
    headsign: str | None
    shape_id: str | None


@dataclass(frozen=True)
class StopTime:
    """Stop time from stop_times.txt."""

    trip_id: str
    stop_sequence: int
    stop_id: str
    arrival_seconds: int  # Seconds since midnight (can be >= 86400 for overnight trips)
    departure_seconds: int | None


@dataclass(frozen=True)
class Shape:
    """Shape point from shapes.txt."""

    shape_id: str
    shape_pt_lat: float
    shape_pt_lon: float
    shape_pt_sequence: int


@dataclass(frozen=True)
class GtfsMeta:
    """Metadata about loaded GTFS static data."""

    agency: str  # Agency identifier (MPK, Mobilis)
    current_hash: str  # SHA256 of the ZIP file
