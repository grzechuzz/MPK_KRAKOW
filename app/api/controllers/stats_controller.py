from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.db import DbSession
from app.api.openapi import openapi_response
from app.api.schemas import (
    EndDateQuery,
    MaxDelayBetweenStopsResponse,
    PunctualityResponse,
    RouteDelayResponse,
    StartDateQuery,
    TrendResponse,
)
from app.api.services.stats_service import StatsService

router = APIRouter(prefix="/lines", tags=["statistics"])

JSON = "application/json"


def _get_service(db: DbSession) -> StatsService:
    return StatsService(db)


Stats = Annotated[StatsService, Depends(_get_service)]


@router.get(
    "/{line_number}/stats/max-delay",
    response_model=None,
    responses=openapi_response(MaxDelayBetweenStopsResponse),
    summary="Max delay generated between consecutive stops",
)
def get_max_delay_between_stops(
    line_number: str,
    service: Stats,
    start_date: StartDateQuery,
    end_date: EndDateQuery,
) -> Response:
    return Response(content=service.max_delay_between_stops(line_number, start_date, end_date), media_type=JSON)


@router.get(
    "/{line_number}/stats/route-delay",
    response_model=None,
    responses=openapi_response(RouteDelayResponse),
    summary="Max delay generated across entire route",
)
def get_route_delay(
    line_number: str,
    service: Stats,
    start_date: StartDateQuery,
    end_date: EndDateQuery,
) -> Response:
    return Response(content=service.route_delay(line_number, start_date, end_date), media_type=JSON)


@router.get(
    "/{line_number}/stats/punctuality",
    response_model=None,
    responses=openapi_response(PunctualityResponse),
    summary="Per-stop punctuality breakdown",
)
def get_punctuality(
    line_number: str,
    service: Stats,
    start_date: StartDateQuery,
    end_date: EndDateQuery,
) -> Response:
    return Response(content=service.punctuality(line_number, start_date, end_date), media_type=JSON)


@router.get(
    "/{line_number}/stats/trend",
    response_model=None,
    responses=openapi_response(TrendResponse),
    summary="Daily average delay trend",
)
def get_trend(
    line_number: str,
    service: Stats,
    start_date: StartDateQuery,
    end_date: EndDateQuery,
) -> Response:
    return Response(content=service.trend(line_number, start_date, end_date), media_type=JSON)
