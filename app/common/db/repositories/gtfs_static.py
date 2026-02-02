from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.common.db.models import CurrentStop, CurrentStopTime, CurrentTrip


class GtfsStaticRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_trip(self, trip_id: str) -> CurrentTrip | None:
        stmt = select(CurrentTrip).options(joinedload(CurrentTrip.route)).where(CurrentTrip.trip_id == trip_id)
        return self._session.scalars(stmt).first()

    def get_trips_by_ids(self, trip_ids: list[str]) -> dict[str, CurrentTrip]:
        if not trip_ids:
            return {}

        stmt = select(CurrentTrip).options(joinedload(CurrentTrip.route)).where(CurrentTrip.trip_id.in_(trip_ids))
        trips = self._session.scalars(stmt).all()
        return {trip.trip_id: trip for trip in trips}

    def get_stop(self, stop_id: str) -> CurrentStop | None:
        return self._session.get(CurrentStop, stop_id)

    def get_stops_by_ids(self, stop_ids: list[str]) -> dict[str, CurrentStop]:
        if not stop_ids:
            return {}

        stmt = select(CurrentStop).where(CurrentStop.stop_id.in_(stop_ids))
        stops = self._session.scalars(stmt).all()
        return {stop.stop_id: stop for stop in stops}

    def get_stop_times_for_trip(self, trip_id: str) -> list[CurrentStopTime]:
        stmt = select(CurrentStopTime).where(CurrentStopTime.trip_id == trip_id).order_by(CurrentStopTime.stop_sequence)

        return list(self._session.scalars(stmt).all())

    def get_stop_times_batch(self, trip_ids: list[str]) -> dict[str, list[CurrentStopTime]]:
        if not trip_ids:
            return {}

        stmt = (
            select(CurrentStopTime)
            .where(CurrentStopTime.trip_id.in_(trip_ids))
            .order_by(CurrentStopTime.trip_id, CurrentStopTime.stop_sequence)
        )

        stop_times = self._session.scalars(stmt).all()
        result: dict[str, list[CurrentStopTime]] = {}

        for st in stop_times:
            if st.trip_id not in result:
                result[st.trip_id] = []
            result[st.trip_id].append(st)

        return result

    def get_max_stop_sequence(self, trip_id: str) -> int | None:
        stmt = select(func.max(CurrentStopTime.stop_sequence)).where(CurrentStopTime.trip_id == trip_id)
        return self._session.scalars(stmt).first()

    def get_stop_sequence_by_stop_id(self, trip_id: str, stop_id: str) -> int | None:
        stmt = select(CurrentStopTime.stop_sequence).where(
            CurrentStopTime.trip_id == trip_id, CurrentStopTime.stop_id == stop_id
        )
        return self._session.scalar(stmt)

    def build_stop_id_to_sequence_map(self, trip_id: str) -> dict[str, int]:
        stop_times = self.get_stop_times_for_trip(trip_id)
        return {st.stop_id: st.stop_sequence for st in stop_times}
