from enum import StrEnum
from typing import Annotated

import msgspec
from fastapi import Query


class Period(StrEnum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"


PeriodQuery = Annotated[Period, Query(description="Data range filter")]


class MaxDelayBetweenStops(msgspec.Struct):
    trip_id: str
    line_number: str
    vehicle_number: str
    from_stop: str
    to_stop: str
    from_sequence: int
    to_sequence: int
    from_planned_time: str
    from_event_time: str
    to_planned_time: str
    to_event_time: str
    delay_generated_seconds: int
    headsign: str
    service_date: str


class MaxDelayBetweenStopsResponse(msgspec.Struct):
    line_number: str
    period: str
    max_delay: list[MaxDelayBetweenStops]
    trips_analyzed: int


class RouteDelay(msgspec.Struct):
    trip_id: str
    line_number: str
    vehicle_number: str
    first_stop: str
    last_stop: str
    first_planned_time: str
    first_event_time: str
    last_planned_time: str
    last_event_time: str
    start_delay_seconds: int
    end_delay_seconds: int
    delay_generated_seconds: int
    headsign: str
    service_date: str


class RouteDelayResponse(msgspec.Struct):
    line_number: str
    period: str
    max_route_delay: list[RouteDelay]
    trips_analyzed: int


class LineSummary(msgspec.Struct):
    line_number: str
    trips_count: int
    avg_delay_seconds: float
    max_delay_seconds: int
    max_delay_between_stops_seconds: int


class LineSummaryResponse(msgspec.Struct):
    period: str
    lines: list[LineSummary]


class PunctualityResponse(msgspec.Struct):
    """
    Thresholds:
    - on_time: delay <= 120s (2 min)
    - slightly_delayed: 120s < delay <= 360s (2-6 min)
    - delayed: delay > 360s (6+ min)
    """

    line_number: str
    period: str
    total_stops: int
    on_time_count: int
    on_time_percent: float
    slightly_delayed_count: int
    slightly_delayed_percent: float
    delayed_count: int
    delayed_percent: float


class TrendDay(msgspec.Struct):
    date: str
    avg_delay_seconds: float
    trips_count: int


class TrendResponse(msgspec.Struct):
    line_number: str
    period: str
    days: list[TrendDay]
