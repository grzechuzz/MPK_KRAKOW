from app.common.gtfs.timeparse import compute_service_date
from app.common.models.enums import Agency, DetectionMethod
from app.common.models.events import StopEvent
from app.common.models.gtfs_realtime import VehiclePosition
from app.common.redis.repositories.saved_sequences import SavedSequencesRepository
from app.common.redis.repositories.trip_updates import TripUpdatesRepository
from app.common.redis.schemas import VehicleState
from app.stop_writer.detector.event_factory import EventFactory
from app.stop_writer.detector.gtfs_cache import GtfsCache


class TripFinalizer:
    def __init__(
        self,
        factory: EventFactory,
        gtfs_cache: GtfsCache,
        saved_seqs: SavedSequencesRepository,
        trip_updates: TripUpdatesRepository,
    ):
        self._factory = factory
        self._cache = gtfs_cache
        self._saved_seqs = saved_seqs
        self._trip_updates = trip_updates

    def finalize(self, prev_state: VehicleState) -> list[StopEvent]:
        events: list[StopEvent] = []
        agency_str = prev_state.agency
        trip_id = prev_state.trip_id

        trip = self._cache.get_trip(trip_id)
        if not trip:
            return events

        max_seq = self._cache.get_max_stop_sequence(trip_id)
        if not max_seq:
            return events

        for seq in range(prev_state.current_stop_sequence + 1, max_seq + 1):
            stop_time = self._cache.get_stop_time(trip_id, seq)
            if not stop_time:
                continue

            service_date = compute_service_date(prev_state.last_timestamp, stop_time.arrival_seconds)

            if self._saved_seqs.is_saved(agency_str, trip_id, service_date, seq):
                continue

            cache = self._trip_updates.get(agency_str, trip_id)
            if not cache:
                continue

            cached_stop = cache.stops.get(seq)
            if not cached_stop:
                continue

            if seq == max_seq:
                event_time = cached_stop.first_seen_arrival
                detection_method = DetectionMethod.TIMEOUT
            else:
                event_time = cached_stop.last_seen_arrival
                detection_method = DetectionMethod.SEQ_JUMP

            is_estimated = detection_method in (DetectionMethod.SEQ_JUMP, DetectionMethod.TIMEOUT)

            dummy_vp = VehiclePosition(
                agency=Agency(agency_str),
                trip_id=trip_id,
                vehicle_id="",
                license_plate=prev_state.license_plate,
                latitude=None,
                longitude=None,
                bearing=None,
                stop_id=stop_time.stop_id,
                stop_sequence=seq,
                status=None,
                timestamp=event_time,
            )

            event = self._factory.create(
                vp=dummy_vp,
                stop_sequence=seq,
                event_time=event_time,
                service_date=service_date,
                trip=trip,
                stop_time=stop_time,
                detection_method=detection_method,
                is_estimated=is_estimated,
            )
            if event:
                events.append(event)

        return events
