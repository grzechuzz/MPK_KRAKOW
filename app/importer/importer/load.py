import csv
import tempfile
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.engine import Connection
from app.common.app_common.gtfs.timeparse import parse_gtfs_time_to_seconds


class LoadError(RuntimeError):
    pass


def load_static_gtfs(conn: Connection, base_dir: str | Path) -> None:
    base_dir = Path(base_dir)

    for name in ("routes.txt", "stops.txt", "trips.txt", "stop_times.txt"):
        p = base_dir / name
        if not p.exists():
            raise LoadError(f"Missing file for load: {p}")

    routes_min = _build_routes_min_csv(base_dir / "routes.txt")
    stops_min = _build_stops_min_csv(base_dir / "stops.txt")
    trips_min = _build_trips_min_csv(base_dir / "trips.txt")
    stop_times_min = _build_stop_times_min_csv(base_dir / "stop_times.txt")

    tmp_files = [routes_min, stops_min, trips_min, stop_times_min]

    try:
        conn.execute(text("TRUNCATE current_stop_times, current_trips, current_stops, current_routes"))

        _copy(conn, "current_routes", routes_min, ["route_id", "route_short_name"])
        _copy(
            conn,
            "current_stops",
            stops_min,
            ["stop_id", "stop_name", "stop_code", "stop_desc", "stop_lat", "stop_lon"],
        )
        _copy(conn, "current_trips", trips_min, ["trip_id", "route_id", "direction_id", "headsign"])
        _copy(
            conn,
            "current_stop_times",
            stop_times_min,
            ["trip_id", "stop_sequence", "stop_id", "arrival_seconds", "departure_seconds"],
        )
    finally:
        for p in tmp_files:
            Path(p).unlink(missing_ok=True)


def _tmp_csv(prefix: str) -> tuple[Path, tempfile._TemporaryFileWrapper]:
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        prefix=prefix,
        suffix=".csv",
        delete=False,
    )
    return Path(tmp.name), tmp


def _require_columns(reader: csv.DictReader, required: set[str], filename: str) -> None:
    if reader.fieldnames is None:
        raise LoadError(f"{filename} has no header row")
    have = set(reader.fieldnames)
    missing = required - have
    if missing:
        raise LoadError(f"{filename} missing columns: {sorted(missing)} (have: {reader.fieldnames})")


def _build_routes_min_csv(routes_txt: Path) -> Path:
    out_path, tmp = _tmp_csv("gtfs_routes_min_")
    try:
        with open(routes_txt, "r", encoding="utf-8", newline="") as f_in, tmp as f_out:
            reader = csv.DictReader(f_in)
            _require_columns(reader, {"route_id", "route_short_name"}, "routes.txt")

            writer = csv.writer(f_out)
            writer.writerow(["route_id", "route_short_name"])

            for row in reader:
                route_id = (row.get("route_id") or "").strip()
                short = (row.get("route_short_name") or "").strip()
                if not route_id or not short:
                    continue
                writer.writerow([route_id, short])

        return out_path
    except Exception as e:
        out_path.unlink(missing_ok=True)
        raise LoadError(f"Failed to transform routes.txt: {e}") from e


def _build_stops_min_csv(stops_txt: Path) -> Path:
    out_path, tmp = _tmp_csv("gtfs_stops_min_")
    try:
        with open(stops_txt, "r", encoding="utf-8", newline="") as f_in, tmp as f_out:
            reader = csv.DictReader(f_in)
            _require_columns(
                reader,
                {"stop_id", "stop_name", "stop_code", "stop_desc", "stop_lat", "stop_lon"},
                "stops.txt",
            )

            writer = csv.writer(f_out)
            writer.writerow(["stop_id", "stop_name", "stop_code", "stop_desc", "stop_lat", "stop_lon"])

            for row in reader:
                stop_id = (row.get("stop_id") or "").strip()
                stop_name = (row.get("stop_name") or "").strip()
                if not stop_id or not stop_name:
                    continue

                stop_code = (row.get("stop_code") or "").strip()
                stop_desc = (row.get("stop_desc") or "").strip()
                stop_lat = (row.get("stop_lat") or "").strip()
                stop_lon = (row.get("stop_lon") or "").strip()

                writer.writerow([
                    stop_id,
                    stop_name,
                    stop_code if stop_code else r"\N",
                    stop_desc if stop_desc else r"\N",
                    stop_lat if stop_lat else r"\N",
                    stop_lon if stop_lon else r"\N",
                ])

        return out_path
    except Exception as e:
        out_path.unlink(missing_ok=True)
        raise LoadError(f"Failed to transform stops.txt: {e}") from e


def _build_trips_min_csv(trips_txt: Path) -> Path:
    out_path, tmp = _tmp_csv("gtfs_trips_min_")
    try:
        with open(trips_txt, "r", encoding="utf-8", newline="") as f_in, tmp as f_out:
            reader = csv.DictReader(f_in)
            _require_columns(reader, {"trip_id", "route_id", "direction_id", "trip_headsign"}, "trips.txt")

            writer = csv.writer(f_out)
            writer.writerow(["trip_id", "route_id", "direction_id", "headsign"])

            for row in reader:
                trip_id = (row.get("trip_id") or "").strip()
                route_id = (row.get("route_id") or "").strip()
                if not trip_id or not route_id:
                    continue

                headsign = (row.get("trip_headsign") or "").strip()
                direction_id = (row.get("direction_id") or "").strip()

                writer.writerow([
                    trip_id,
                    route_id,
                    direction_id if direction_id else r"\N",
                    headsign if headsign else r"\N",
                ])

        return out_path
    except Exception as e:
        out_path.unlink(missing_ok=True)
        raise LoadError(f"Failed to transform trips.txt: {e}") from e


def _build_stop_times_min_csv(stop_times_txt: Path) -> Path:
    out_path, tmp = _tmp_csv("gtfs_stop_times_min_")
    try:
        with open(stop_times_txt, "r", encoding="utf-8", newline="") as f_in, tmp as f_out:
            reader = csv.DictReader(f_in)
            _require_columns(
                reader,
                {"trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"},
                "stop_times.txt",
            )

            writer = csv.writer(f_out)
            writer.writerow(["trip_id", "stop_sequence", "stop_id", "arrival_seconds", "departure_seconds"])

            for row in reader:
                trip_id = (row.get("trip_id") or "").strip()
                stop_id = (row.get("stop_id") or "").strip()
                stop_sequence = (row.get("stop_sequence") or "").strip()
                arrival_time = row.get("arrival_time")

                if not trip_id or not stop_id or not stop_sequence:
                    continue

                if arrival_time is None or arrival_time.strip() == "":
                    raise LoadError(f"stop_times has empty arrival_time for trip_id={trip_id}, seq={stop_sequence}")

                arrival_seconds = parse_gtfs_time_to_seconds(arrival_time)

                dep_raw = (row.get("departure_time") or "").strip()
                dep_seconds = parse_gtfs_time_to_seconds(dep_raw) if dep_raw else None

                writer.writerow([
                    trip_id,
                    stop_sequence,
                    stop_id,
                    arrival_seconds,
                    dep_seconds if dep_seconds is not None else r"\N",
                ])

        return out_path
    except Exception as e:
        out_path.unlink(missing_ok=True)
        raise LoadError(f"Failed to transform stop_times.txt: {e}") from e


def _copy(conn, table: str, file: Path, columns: list[str]) -> None:
    cols = ", ".join(columns)
    sql = f"COPY {table} ({cols}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '\\N')"

    try:
        raw = conn.connection
        with raw.cursor() as cur, open(file, "r", encoding="utf-8", newline="") as f:
            with cur.copy(sql) as copy:
                for line in f:
                    copy.write(line)
    except OSError as e:
        raise LoadError(f"Failed to read {file}: {e}") from e
    except Exception as e:
        raise LoadError(f"COPY into {table} failed from {file}: {e}") from e
