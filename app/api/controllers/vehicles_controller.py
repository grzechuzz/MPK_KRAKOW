from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.db import DbSession
from app.api.openapi import openapi_response
from app.api.schemas import LiveVehicleResponse
from app.api.services.vehicles_service import VehiclesService

router = APIRouter(prefix="/vehicles", tags=["live"])

JSON = "application/json"


def _get_service(db: DbSession) -> VehiclesService:
    return VehiclesService(db)


Vehicles = Annotated[VehiclesService, Depends(_get_service)]


@router.get("/positions", responses=openapi_response(LiveVehicleResponse), summary="Live vehicle positions")
def get_positions(service: Vehicles) -> Response:
    """Returns all currently active vehicles (MPK + Mobilis) with GPS coordinates, line number, and headsign."""
    return Response(content=service.get_live_vehicles(), media_type=JSON)
