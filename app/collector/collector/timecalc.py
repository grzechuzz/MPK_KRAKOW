from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class PlannedTimes:
    service_date: date
    planned_time: datetime
    planned_seconds: int
    day_offset: int


def compute_service_date_from_start_date(start_date_yyyymmdd: str) -> date:
    y = int(start_date_yyyymmdd[0:4])
    m = int(start_date_yyyymmdd[4:6])
    d = int(start_date_yyyymmdd[6:8])
    return date(y, m, d)


def compute_planned_times(
    service_date: date,
    arrival_seconds: int,
    tz: ZoneInfo,
) -> PlannedTimes:
    day_offset = arrival_seconds // 86400
    sec_in_day = arrival_seconds % 86400

    planned_dt = datetime(
        service_date.year, service_date.month, service_date.day, tzinfo=tz
    ) + timedelta(days=day_offset, seconds=sec_in_day)

    return PlannedTimes(
        service_date=service_date,
        planned_time=planned_dt,
        planned_seconds=sec_in_day,
        day_offset=day_offset,
    )


def compute_delay_seconds(event_time: datetime, planned_time: datetime) -> int:
    return int((event_time - planned_time).total_seconds())
