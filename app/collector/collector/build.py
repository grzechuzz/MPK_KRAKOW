from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.collector.collector.parse import VPItem
from app.collector.collector.static_lookup import StaticStop, StaticStopTime, StaticTrip
from app.collector.collector.timecalc import compute_delay_seconds, compute_planned_times

# GTFS-RT enum values:
# 0 = INCOMING_AT
# 1 = STOPPED_AT
# 2 = IN_TRANSIT_TO
STOPPED_AT = 1

NEGATIVE_DELAY_CUTOFF_SECONDS = -30


@dataclass(frozen=True)
class BuiltStopEvent:
    line_number: str
    stop_name: str
    stop_sequence: int
    direction_id: int | None
    planned_time: datetime
    event_time: datetime
    delay_seconds: int
    vehicle_label: str | None  # license_plate
    is_estimated: bool
    headsign: str | None
    service_date: date
    trip_id: str
    stop_id: str
    static_hash: str


def build_stop_events(
    items: list[VPItem],
    trips_by_id: dict[str, StaticTrip],
    stoptimes_by_key: dict[tuple[str, int], StaticStopTime],
    stops_by_id: dict[str, StaticStop],
    static_hash: str,
    tz: ZoneInfo,
) -> list[BuiltStopEvent]:
    out: list[BuiltStopEvent] = []

    for it in items:
        if it.status != STOPPED_AT:
            continue

        if it.stop_sequence is None:
            continue
        if not it.rt_timestamp:
            continue

        st_trip = trips_by_id.get(it.trip_id)
        if not st_trip:
            continue

        st_st = stoptimes_by_key.get((it.trip_id, int(it.stop_sequence)))
        if not st_st:
            continue

        stop_id = st_st.stop_id
        st_stop = stops_by_id.get(stop_id)
        if not st_stop:
            continue

        event_time = datetime.fromtimestamp(int(it.rt_timestamp), tz=ZoneInfo("UTC")).astimezone(tz)

        sched_seconds = (
            int(st_st.departure_seconds)
            if st_st.departure_seconds is not None
            else int(st_st.arrival_seconds)
        )

        service_date = event_time.date()
        if sched_seconds >= 86400:
            service_date = service_date - timedelta(days=1)

        planned = compute_planned_times(service_date, sched_seconds, tz)
        delay_seconds = compute_delay_seconds(event_time, planned.planned_time)

        if delay_seconds < NEGATIVE_DELAY_CUTOFF_SECONDS:
            continue

        out.append(
            BuiltStopEvent(
                line_number=st_trip.line_number,
                stop_name=st_stop.stop_name,
                stop_sequence=int(it.stop_sequence),
                direction_id=st_trip.direction_id,
                planned_time=planned.planned_time,
                event_time=event_time,
                delay_seconds=delay_seconds,
                vehicle_label=it.vehicle_license_plate,  # license_plate -> vehicle_label
                is_estimated=False,
                headsign=st_trip.headsign,
                service_date=service_date,
                trip_id=it.trip_id,
                stop_id=stop_id,
                static_hash=static_hash,
            )
        )

    return out
