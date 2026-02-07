from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.common.db.models import CurrentStop, CurrentStopTime, CurrentTrip


class GtfsStaticRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_trip(self, trip_id: str) -> CurrentTrip | None:
        stmt = select(CurrentTrip).options(joinedload(CurrentTrip.route)).where(CurrentTrip.trip_id == trip_id)
        return self._session.scalars(stmt).first()

    def get_stop(self, stop_id: str) -> CurrentStop | None:
        return self._session.get(CurrentStop, stop_id)

    def get_stop_times_for_trip(self, trip_id: str) -> list[CurrentStopTime]:
        stmt = select(CurrentStopTime).where(CurrentStopTime.trip_id == trip_id).order_by(CurrentStopTime.stop_sequence)

        return list(self._session.scalars(stmt).all())

    def get_max_stop_sequence(self, trip_id: str) -> int | None:
        stmt = select(func.max(CurrentStopTime.stop_sequence)).where(CurrentStopTime.trip_id == trip_id)
        return self._session.scalars(stmt).first()

    def build_stop_id_to_sequence_map(self, trip_id: str) -> dict[str, int]:
        stop_times = self.get_stop_times_for_trip(trip_id)
        return {st.stop_id: st.stop_sequence for st in stop_times}
