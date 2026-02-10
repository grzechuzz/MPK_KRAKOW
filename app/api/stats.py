from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.db import DbSession
from app.api.repository import StatsRepository, resolve_date_range
from app.api.schemas import (
    LineSummary,
    LineSummaryResponse,
    MaxDelayBetweenStops,
    MaxDelayBetweenStopsResponse,
    Period,
    PeriodQuery,
    PunctualityResponse,
    RouteDelay,
    RouteDelayResponse,
    TrendDay,
    TrendResponse,
)

router = APIRouter(prefix="/lines", tags=["statistics"])


def _to_str(row: dict[str, Any]) -> dict[str, Any]:
    return {k: str(v) if not isinstance(v, (str, int, float)) else v for k, v in row.items()}


def _check_line_exists(trips: int, line_number: str, period: Period) -> None:
    if not trips:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Line {line_number} not found in {period.value} period"
        )


@router.get("/{line_number}/stats/max-delay-between-stops")
def get_max_delay_between_stops(
    line_number: str,
    db: DbSession,
    period: PeriodQuery = Period.TODAY,
) -> MaxDelayBetweenStopsResponse:
    start, end = resolve_date_range(period)
    repo = StatsRepository(db)

    trips = repo.trips_count(line_number, start, end)
    _check_line_exists(trips, line_number, period)

    rows = repo.max_delay_between_stops(line_number, start, end)

    return MaxDelayBetweenStopsResponse(
        line_number=line_number,
        period=period.value,
        max_delay=[MaxDelayBetweenStops(**_to_str(row)) for row in rows],
        trips_analyzed=trips,
    )


@router.get("/{line_number}/stats/route-delay")
def get_route_delay(
    line_number: str,
    db: DbSession,
    period: PeriodQuery = Period.TODAY,
) -> RouteDelayResponse:
    start, end = resolve_date_range(period)
    repo = StatsRepository(db)

    trips = repo.trips_count(line_number, start, end)
    _check_line_exists(trips, line_number, period)

    rows = repo.max_route_delay(line_number, start, end)

    return RouteDelayResponse(
        line_number=line_number,
        period=period.value,
        max_route_delay=[RouteDelay(**_to_str(row)) for row in rows],
        trips_analyzed=trips,
    )


@router.get("/stats/summary")
def get_lines_summary(
    db: DbSession,
    period: PeriodQuery = Period.TODAY,
) -> LineSummaryResponse:
    start, end = resolve_date_range(period)
    repo = StatsRepository(db)

    rows = repo.lines_summary(start, end)

    return LineSummaryResponse(
        period=period.value,
        lines=[LineSummary(**_to_str(r)) for r in rows],
    )


@router.get("/{line_number}/stats/punctuality")
def get_punctuality(
    line_number: str,
    db: DbSession,
    period: PeriodQuery = Period.TODAY,
) -> PunctualityResponse:
    start, end = resolve_date_range(period)
    repo = StatsRepository(db)

    trips = repo.trips_count(line_number, start, end)
    _check_line_exists(trips, line_number, period)

    row = repo.punctuality(line_number, start, end)
    total = row["total"]

    return PunctualityResponse(
        line_number=line_number,
        period=period.value,
        total_trips=total,
        on_time_count=row["on_time"],
        on_time_percent=round(row["on_time"] / total * 100, 1) if total else 0.0,
        slightly_delayed_count=row["slightly_delayed"],
        slightly_delayed_percent=round(row["slightly_delayed"] / total * 100, 1) if total else 0.0,
        delayed_count=row["delayed"],
        delayed_percent=round(row["delayed"] / total * 100, 1) if total else 0.0,
    )


@router.get("/{line_number}/stats/trend")
def get_trend(
    line_number: str,
    db: DbSession,
    period: PeriodQuery = Period.MONTH,
) -> TrendResponse:
    start, end = resolve_date_range(period)
    repo = StatsRepository(db)

    trips = repo.trips_count(line_number, start, end)
    _check_line_exists(trips, line_number, period)

    rows = repo.trend(line_number, start, end)

    return TrendResponse(
        line_number=line_number,
        period=period.value,
        days=[TrendDay(**_to_str(r)) for r in rows],
    )
