from dataclasses import dataclass
from typing import Iterable
from sqlalchemy import text


@dataclass(frozen=True)
class StaticTrip:
    trip_id: str
    route_id: str
    direction_id: int | None
    headsign: str | None
    line_number: str


@dataclass(frozen=True)
class StaticStopTime:
    trip_id: str
    stop_sequence: int
    stop_id: str
    arrival_seconds: int
    departure_seconds: int | None


@dataclass(frozen=True)
class StaticStop:
    stop_id: str
    stop_name: str


def fetch_static_for_vp(
    conn,
    trip_ids: Iterable[str],
    stop_ids: Iterable[str],
    trip_seq_pairs: Iterable[tuple[str, int]],
) -> tuple[
    dict[str, StaticTrip],
    dict[tuple[str, int], StaticStopTime],
    dict[str, StaticStop],
]:
    trip_ids = list(dict.fromkeys(trip_ids))
    stop_ids = list(dict.fromkeys(stop_ids))
    trip_seq_pairs = list(dict.fromkeys(trip_seq_pairs))

    trips_by_id: dict[str, StaticTrip] = {}
    stoptimes_by_key: dict[tuple[str, int], StaticStopTime] = {}
    stops_by_id: dict[str, StaticStop] = {}

    # 1) Trips + line_number (join current_routes)
    if trip_ids:
        q = text(
            """
            SELECT
                t.trip_id,
                t.route_id,
                t.direction_id,
                t.headsign,
                r.route_short_name AS line_number
            FROM current_trips t
            JOIN current_routes r ON r.route_id = t.route_id
            WHERE t.trip_id = ANY(:trip_ids)
            """
        )
        rows = conn.execute(q, {"trip_ids": trip_ids}).mappings().all()
        for row in rows:
            trips_by_id[row["trip_id"]] = StaticTrip(
                trip_id=row["trip_id"],
                route_id=row["route_id"],
                direction_id=row["direction_id"],
                headsign=row["headsign"],
                line_number=row["line_number"],
            )

    # 2) Stops (stop_name)
    if stop_ids:
        q = text(
            """
            SELECT stop_id, stop_name
            FROM current_stops
            WHERE stop_id = ANY(:stop_ids)
            """
        )
        rows = conn.execute(q, {"stop_ids": stop_ids}).mappings().all()
        for row in rows:
            stops_by_id[row["stop_id"]] = StaticStop(
                stop_id=row["stop_id"],
                stop_name=row["stop_name"],
            )

    # 3) Stop times  (trip_id, stop_sequence)
    if trip_seq_pairs:
        values_sql_parts: list[str] = []
        params: dict[str, object] = {}
        for i, (tid, seq) in enumerate(trip_seq_pairs):
            values_sql_parts.append(f"(:t{i}, :s{i})")
            params[f"t{i}"] = tid
            params[f"s{i}"] = int(seq)

        values_sql = ", ".join(values_sql_parts)

        q = text(
            f"""
            WITH wanted(trip_id, stop_sequence) AS (
                VALUES {values_sql}
            )
            SELECT
                st.trip_id,
                st.stop_sequence,
                st.stop_id,
                st.arrival_seconds,
                st.departure_seconds
            FROM current_stop_times st
            JOIN wanted w
              ON w.trip_id = st.trip_id
             AND w.stop_sequence = st.stop_sequence
            """
        )
        rows = conn.execute(q, params).mappings().all()
        for row in rows:
            key = (row["trip_id"], int(row["stop_sequence"]))
            stoptimes_by_key[key] = StaticStopTime(
                trip_id=row["trip_id"],
                stop_sequence=int(row["stop_sequence"]),
                stop_id=row["stop_id"],
                arrival_seconds=int(row["arrival_seconds"]),
                departure_seconds=int(row["departure_seconds"]) if row["departure_seconds"] is not None else None,
            )

    return trips_by_id, stoptimes_by_key, stops_by_id
