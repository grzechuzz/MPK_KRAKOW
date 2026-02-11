from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.db import DbSession
from app.api.schemas import Period, PeriodQuery
from app.api.service import StatsService

router = APIRouter(prefix="/lines", tags=["statistics"])

JSON = "application/json"


def _get_stats_service(db: DbSession) -> StatsService:
    return StatsService(db)


Stats = Annotated[StatsService, Depends(_get_stats_service)]


@router.get("/{line_number}/stats/max-delay-between-stops")
def get_max_delay_between_stops(
    line_number: str,
    service: Stats,
    period: PeriodQuery = Period.TODAY,
) -> Response:
    return Response(content=service.max_delay_between_stops(line_number, period), media_type=JSON)


@router.get("/{line_number}/stats/route-delay")
def get_route_delay(
    line_number: str,
    service: Stats,
    period: PeriodQuery = Period.TODAY,
) -> Response:
    return Response(content=service.route_delay(line_number, period), media_type=JSON)


@router.get("/stats/summary")
def get_lines_summary(
    service: Stats,
    period: PeriodQuery = Period.TODAY,
) -> Response:
    return Response(content=service.lines_summary(period), media_type=JSON)


@router.get("/{line_number}/stats/punctuality")
def get_punctuality(
    line_number: str,
    service: Stats,
    period: PeriodQuery = Period.TODAY,
) -> Response:
    return Response(content=service.punctuality(line_number, period), media_type=JSON)


@router.get("/{line_number}/stats/trend")
def get_trend(
    line_number: str,
    service: Stats,
    period: PeriodQuery = Period.MONTH,
) -> Response:
    return Response(content=service.trend(line_number, period), media_type=JSON)
