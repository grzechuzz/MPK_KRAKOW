import csv
import io
import logging
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.gtfs.timeparse import parse_gtfs_time_to_seconds

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TableMapping:
    """Configuration for loading a GTFS file into a database table."""

    gtfs_file: str
    table_name: str
    columns: list[str]
    row_transformer: Callable[[dict[str, str], str], list[Any]]


def _routes_transformer(row: dict[str, str], agency_id: str) -> list[Any]:
    return [row["route_id"], agency_id, row["route_short_name"]]


def _stops_transformer(row: dict[str, str], agency_id: str) -> list[Any]:
    return [
        row["stop_id"],
        agency_id,
        row["stop_name"],
        row["stop_code"],
        row["stop_desc"],
        row["stop_lat"],
        row["stop_lon"],
    ]


def _trips_transformer(row: dict[str, str], agency_id: str) -> list[Any]:
    return [
        row["trip_id"],
        row["route_id"],
        agency_id,
        row["service_id"],
        row["direction_id"],
        row["trip_headsign"],
        row["shape_id"],
    ]


def _stop_times_transformer(row: dict[str, str], agency_id: str) -> list[Any]:
    return [
        row["trip_id"],
        row["stop_sequence"],
        row["stop_id"],
        agency_id,
        parse_gtfs_time_to_seconds(row["arrival_time"]),
        parse_gtfs_time_to_seconds(row["departure_time"]),
    ]


def _shapes_transformer(row: dict[str, str], agency_id: str) -> list[Any]:
    return [agency_id, row["shape_id"], row["shape_pt_lat"], row["shape_pt_lon"], row["shape_pt_sequence"]]


TABLE_MAPPINGS = [
    TableMapping("routes.txt", "current_routes", ["route_id", "agency_id", "route_short_name"], _routes_transformer),
    TableMapping(
        "stops.txt",
        "current_stops",
        ["stop_id", "agency_id", "stop_name", "stop_code", "stop_desc", "stop_lat", "stop_lon"],
        _stops_transformer,
    ),
    TableMapping(
        "trips.txt",
        "current_trips",
        ["trip_id", "route_id", "agency_id", "service_id", "direction_id", "headsign", "shape_id"],
        _trips_transformer,
    ),
    TableMapping(
        "stop_times.txt",
        "current_stop_times",
        ["trip_id", "stop_sequence", "stop_id", "agency_id", "arrival_seconds", "departure_seconds"],
        _stop_times_transformer,
    ),
    TableMapping(
        "shapes.txt",
        "current_shapes",
        ["agency_id", "shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"],
        _shapes_transformer,
    ),
]


_DELETE_ORDER = [
    "current_stop_times",
    "current_shapes",
    "current_trips",
    "current_stops",
    "current_routes",
]


def _delete_agency_data(session: Session, agency_id: str) -> None:
    """Delete all GTFS data for a specific agency."""
    logger.info(f"[{agency_id}] Deleting old data...")

    for table_name in _DELETE_ORDER:
        session.execute(text(f"DELETE FROM {table_name} WHERE agency_id = :agency_id"), {"agency_id": agency_id})

    session.flush()
    logger.info(f"[{agency_id}] Delete complete")


def _copy_to_table(session: Session, table_name: str, columns: list[str], data: io.StringIO) -> None:
    """Bulk load via COPY."""
    raw_conn = session.connection().connection.dbapi_connection
    if raw_conn is None:
        raise RuntimeError("No database connection available")

    cursor = raw_conn.cursor()
    data.seek(0)

    with cursor.copy(f"COPY {table_name} ({','.join(columns)}) FROM STDIN WITH (FORMAT CSV)") as copy:
        copy.write(data.getvalue())


def _load_table(session: Session, zf: zipfile.ZipFile, mapping: TableMapping, agency_id: str) -> None:
    """Load a single GTFS file into its corresponding database table."""
    logger.info(f"[{agency_id}] Loading {mapping.gtfs_file}...")

    buf = io.StringIO()
    writer = csv.writer(buf)

    with zf.open(mapping.gtfs_file) as f:
        reader = csv.DictReader(line.decode("utf-8-sig") for line in f)
        for row in reader:
            writer.writerow(mapping.row_transformer(row, agency_id))

    _copy_to_table(session, mapping.table_name, mapping.columns, buf)


def load_gtfs_zip(session: Session, zip_path: Path, agency_id: str) -> None:
    """Load GTFS static data."""
    logger.info(f"[{agency_id}] Opening ZIP: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        _delete_agency_data(session, agency_id)

        for mapping in TABLE_MAPPINGS:
            _load_table(session, zf, mapping, agency_id)

        logger.info(f"[{agency_id}] All data loaded, committing...")
