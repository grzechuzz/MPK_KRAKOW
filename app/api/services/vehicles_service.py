import msgspec
from sqlalchemy.orm import Session

from app.api.repositories.vehicles_repository import VehiclesRepository
from app.api.schemas import LiveVehicle, LiveVehicleResponse
from app.common.db.repositories.gtfs_static import GtfsStaticRepository


class VehiclesService:
    def __init__(self, db: Session):
        self._static_repo = GtfsStaticRepository(db)
        self._vehicles_repo = VehiclesRepository()

    def get_live_vehicles(self) -> bytes:
        positions = self._vehicles_repo.fetch_all_positions()
        trip_info = self._static_repo.get_all_trip_info()

        vehicles: list[LiveVehicle] = []
        for vp in positions:
            if not vp.has_position or not vp.license_plate:
                continue

            info = trip_info.get(vp.trip_id)
            if not info:
                continue

            line_number, headsign, shape_id = info

            vehicles.append(
                LiveVehicle(
                    trip_id=vp.trip_id,
                    license_plate=vp.license_plate,
                    line_number=line_number,
                    headsign=headsign,
                    shape_id=shape_id,
                    latitude=vp.latitude,  # type: ignore[arg-type]
                    longitude=vp.longitude,  # type: ignore[arg-type]
                    bearing=vp.bearing,
                    timestamp=vp.timestamp.isoformat(),
                )
            )

        return msgspec.json.encode(LiveVehicleResponse(count=len(vehicles), vehicles=vehicles))
