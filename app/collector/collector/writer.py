from collections.abc import Iterable
from dataclasses import asdict

from sqlalchemy import text

from app.collector.collector.build import BuiltStopEvent

_INSERT_STOP_EVENTS = text(
    """
    INSERT INTO stop_events (
        line_number,
        stop_name,
        stop_sequence,
        direction_id,
        planned_time,
        event_time,
        delay_seconds,
        vehicle_label,
        is_estimated,
        headsign,
        service_date,
        trip_id,
        stop_id,
        static_hash
    )
    VALUES (
        :line_number,
        :stop_name,
        :stop_sequence,
        :direction_id,
        :planned_time,
        :event_time,
        :delay_seconds,
        :vehicle_label,
        :is_estimated,
        :headsign,
        :service_date,
        :trip_id,
        :stop_id,
        :static_hash
    )
    ON CONFLICT (trip_id, service_date, stop_sequence) DO NOTHING
    """
)


def insert_stop_events(conn, events: Iterable[BuiltStopEvent]) -> int:
    rows = []
    for e in events:
        d = asdict(e)
        rows.append(d)

    if not rows:
        return 0

    res = conn.execute(_INSERT_STOP_EVENTS, rows)
    return int(res.rowcount or 0)
