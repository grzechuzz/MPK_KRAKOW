import csv
import io
import logging
import zipfile
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.common.db.models import CurrentRoute, CurrentShape, CurrentStop, CurrentStopTime, CurrentTrip
from app.common.gtfs.timeparse import parse_gtfs_time_to_seconds

logger = logging.getLogger(__name__)


def _delete_agency_data(session: Session, agency_id: str) -> None:
    """Delete all GTFS data for a specific agency."""
    logger.info(f"[{agency_id}] Deleting old data...")

    routes_subq = select(CurrentRoute.route_id).where(CurrentRoute.agency_id == agency_id)
    trips_subq = select(CurrentTrip.trip_id).where(CurrentTrip.route_id.in_(routes_subq))
    stops_subq = select(CurrentStopTime.stop_id.distinct()).where(CurrentStopTime.trip_id.in_(trips_subq))

    session.execute(delete(CurrentStopTime).where(CurrentStopTime.trip_id.in_(trips_subq)))
    session.execute(delete(CurrentStop).where(CurrentStop.stop_id.in_(stops_subq)))
    session.execute(delete(CurrentTrip).where(CurrentTrip.route_id.in_(routes_subq)))
    session.execute(delete(CurrentRoute).where(CurrentRoute.agency_id == agency_id))
    session.execute(delete(CurrentShape).where(CurrentShape.agency_id == agency_id))

    session.flush()
    logger.info(f"[{agency_id}] Delete complete")


def _copy_from_csv(session: Session, table_name: str, columns: list[str], data: io.StringIO) -> None:
    """Use PostgreSQL COPY for fast bulk insert."""
    raw_conn = session.connection().connection.dbapi_connection
    cursor = raw_conn.cursor()
    data.seek(0)

    with cursor.copy(f"COPY {table_name} ({','.join(columns)}) FROM STDIN WITH (FORMAT CSV)") as copy:
        copy.write(data.getvalue())


def load_gtfs_zip(session: Session, zip_path: Path, agency_id: str) -> None:
    """Load GTFS static data"""
    logger.info(f"[{agency_id}] Opening ZIP: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        _delete_agency_data(session, agency_id)

        logger.info(f"[{agency_id}] Loading routes...")
        buf = io.StringIO()
        writer = csv.writer(buf)
        with zf.open("routes.txt") as f:
            reader = csv.DictReader(line.decode("utf-8-sig") for line in f)
            for row in reader:
                writer.writerow([row["route_id"], agency_id, row["route_short_name"]])
        _copy_from_csv(session, "current_routes", ["route_id", "agency_id", "route_short_name"], buf)

        logger.info(f"[{agency_id}] Loading stops...")
        buf = io.StringIO()
        writer = csv.writer(buf)
        with zf.open("stops.txt") as f:
            reader = csv.DictReader(line.decode("utf-8-sig") for line in f)
            for row in reader:
                writer.writerow(
                    [
                        row["stop_id"],
                        row["stop_name"],
                        row["stop_code"],
                        row["stop_desc"],
                        row["stop_lat"],
                        row["stop_lon"],
                    ]
                )
        _copy_from_csv(
            session, "current_stops", ["stop_id", "stop_name", "stop_code", "stop_desc", "stop_lat", "stop_lon"], buf
        )

        logger.info(f"[{agency_id}] Loading trips...")
        buf = io.StringIO()
        writer = csv.writer(buf)
        with zf.open("trips.txt") as f:
            reader = csv.DictReader(line.decode("utf-8-sig") for line in f)
            for row in reader:
                writer.writerow(
                    [
                        row["trip_id"],
                        row["route_id"],
                        row["service_id"],
                        row["direction_id"],
                        row["trip_headsign"],
                        row["shape_id"],
                    ]
                )
        _copy_from_csv(
            session, "current_trips", ["trip_id", "route_id", "service_id", "direction_id", "headsign", "shape_id"], buf
        )

        logger.info(f"[{agency_id}] Loading stop_times...")
        buf = io.StringIO()
        writer = csv.writer(buf)
        with zf.open("stop_times.txt") as f:
            reader = csv.DictReader(line.decode("utf-8-sig") for line in f)
            for row in reader:
                writer.writerow(
                    [
                        row["trip_id"],
                        row["stop_sequence"],
                        row["stop_id"],
                        parse_gtfs_time_to_seconds(row["arrival_time"]),
                        parse_gtfs_time_to_seconds(row["departure_time"]),
                    ]
                )
        _copy_from_csv(
            session,
            "current_stop_times",
            ["trip_id", "stop_sequence", "stop_id", "arrival_seconds", "departure_seconds"],
            buf,
        )

        logger.info(f"[{agency_id}] Loading shapes...")
        buf = io.StringIO()
        writer = csv.writer(buf)
        with zf.open("shapes.txt") as f:
            reader = csv.DictReader(line.decode("utf-8-sig") for line in f)
            for row in reader:
                writer.writerow(
                    [agency_id, row["shape_id"], row["shape_pt_lat"], row["shape_pt_lon"], row["shape_pt_sequence"]]
                )
        _copy_from_csv(
            session,
            "current_shapes",
            ["agency_id", "shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"],
            buf,
        )

        logger.info(f"[{agency_id}] All data loaded, committing...")
