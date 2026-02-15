from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api import schemas_docs as docs
from app.api.db import DbSession
from app.api.services.vehicles_service import VehiclesService

router = APIRouter(prefix="/vehicles", tags=["live"])

JSON = "application/json"


def _get_service(db: DbSession) -> VehiclesService:
    return VehiclesService(db)


Vehicles = Annotated[VehiclesService, Depends(_get_service)]


@router.get("/positions", response_model=docs.LiveVehicleResponse, summary="Live vehicle positions")
def get_positions(service: Vehicles) -> Response:
    """
    Returns current GPS coordinates for all active vehicles (MPK + Mobilis).

    ### Timezone (UTC)
    The timestamp field is provided in UTC (ISO 8601) format (e.g., 2026-02-15T17:07:00+00:00).
    """
    return Response(content=service.get_live_vehicles(), media_type=JSON)
