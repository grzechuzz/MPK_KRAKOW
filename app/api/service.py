from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api import cache
from app.api.repository import StatsRepository, resolve_date_range
from app.api.schemas import (
    LineSummary,
    LineSummaryResponse,
    MaxDelayBetweenStops,
    MaxDelayBetweenStopsResponse,
    Period,
    PunctualityResponse,
    RouteDelay,
    RouteDelayResponse,
    TrendDay,
    TrendResponse,
)


def _to_str(row: dict[str, Any]) -> dict[str, Any]:
    return {k: str(v) if not isinstance(v, (str, int, float)) else v for k, v in row.items()}


def _check_line_exists(trips: int, line_number: str, period: Period) -> None:
    if not trips:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Line {line_number} not found in {period.value} period",
        )


class StatsService:
    def __init__(self, db: Session):
        self._repo = StatsRepository(db)

    def max_delay_between_stops(self, line_number: str, period: Period) -> bytes:
        cached = cache.get_cached("max-delay-between-stops", period, line_number)
        if cached is not None:
            return cached

        start, end = resolve_date_range(period)

        trips = self._repo.trips_count(line_number, start, end)
        _check_line_exists(trips, line_number, period)

        rows = self._repo.max_delay_between_stops(line_number, start, end)

        result = MaxDelayBetweenStopsResponse(
            line_number=line_number,
            period=period.value,
            max_delay=[MaxDelayBetweenStops(**_to_str(row)) for row in rows],
            trips_analyzed=trips,
        )
        return cache.set_cached("max-delay-between-stops", period, result, line_number)

    def route_delay(self, line_number: str, period: Period) -> bytes:
        cached = cache.get_cached("route-delay", period, line_number)
        if cached is not None:
            return cached

        start, end = resolve_date_range(period)

        trips = self._repo.trips_count(line_number, start, end)
        _check_line_exists(trips, line_number, period)

        rows = self._repo.max_route_delay(line_number, start, end)

        result = RouteDelayResponse(
            line_number=line_number,
            period=period.value,
            max_route_delay=[RouteDelay(**_to_str(row)) for row in rows],
            trips_analyzed=trips,
        )
        return cache.set_cached("route-delay", period, result, line_number)

    def lines_summary(self, period: Period) -> bytes:
        cached = cache.get_cached("summary", period)
        if cached is not None:
            return cached

        start, end = resolve_date_range(period)
        rows = self._repo.lines_summary(start, end)

        result = LineSummaryResponse(
            period=period.value,
            lines=[LineSummary(**_to_str(r)) for r in rows],
        )
        return cache.set_cached("summary", period, result)

    def punctuality(self, line_number: str, period: Period) -> bytes:
        cached = cache.get_cached("punctuality", period, line_number)
        if cached is not None:
            return cached

        start, end = resolve_date_range(period)

        trips = self._repo.trips_count(line_number, start, end)
        _check_line_exists(trips, line_number, period)

        row = self._repo.punctuality(line_number, start, end)
        total = row["total"]

        result = PunctualityResponse(
            line_number=line_number,
            period=period.value,
            total_stops=total,
            on_time_count=row["on_time"],
            on_time_percent=round(row["on_time"] / total * 100, 1) if total else 0.0,
            slightly_delayed_count=row["slightly_delayed"],
            slightly_delayed_percent=round(row["slightly_delayed"] / total * 100, 1) if total else 0.0,
            delayed_count=row["delayed"],
            delayed_percent=round(row["delayed"] / total * 100, 1) if total else 0.0,
        )
        return cache.set_cached("punctuality", period, result, line_number)

    def trend(self, line_number: str, period: Period) -> bytes:
        cached = cache.get_cached("trend", period, line_number)
        if cached is not None:
            return cached

        start, end = resolve_date_range(period)

        trips = self._repo.trips_count(line_number, start, end)
        _check_line_exists(trips, line_number, period)

        rows = self._repo.trend(line_number, start, end)

        result = TrendResponse(
            line_number=line_number,
            period=period.value,
            days=[TrendDay(**_to_str(r)) for r in rows],
        )
        return cache.set_cached("trend", period, result, line_number)
