from datetime import datetime, timezone
from google.transit import gtfs_realtime_pb2

from app.common.models.enums import Agency, VehicleStatus
from app.common.models.gtfs_realtime import StopTimeUpdate, TripUpdate, VehiclePosition


def parse_vehicle_positions(pb_data: bytes, agency: Agency) -> list[VehiclePosition]:
    """
    Parse vehicle positions from VehiclePositions.pb feed.
    """
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(pb_data)

    results: list[VehiclePosition] = []

    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue

        v = entity.vehicle

        if not v.HasField("trip") or not v.trip.trip_id:
            continue

        vehicle_id = None
        license_plate = None

        if v.HasField("vehicle"):
            vehicle_id = v.vehicle.id or None
            license_plate = v.vehicle.license_plate or None

        if not license_plate:
            continue

        latitude = None
        longitude = None
        bearing = None
        if v.HasField("position"):
            latitude = v.position.latitude or None
            longitude = v.position.longitude or None
            bearing = v.position.bearing if v.position.HasField("bearing") else None

        stop_id = v.stop_id or None
        stop_sequence = int(v.current_stop_sequence) if v.HasField("current_stop_sequence") else None
        status = VehicleStatus.from_int(int(v.current_status)) if v.HasField("current_status") else None

        ts = v.timestamp if v.timestamp else None
        if not ts:
            continue
        timestamp = datetime.fromtimestamp(ts, tz=timezone.utc)

        results.append(
            VehiclePosition(
                agency=agency,
                trip_id=v.trip.trip_id,
                vehicle_id=vehicle_id or "",
                license_plate=license_plate,
                latitude=latitude,
                longitude=longitude,
                bearing=bearing,
                stop_id=stop_id,
                stop_sequence=stop_sequence,
                status=status,
                timestamp=timestamp,
            )
        )

    return results


def parse_trip_updates(pb_data: bytes, agency: Agency) -> list[TripUpdate]:
    """
        Parse trip updates from TripUpdates.pb feed.
    """
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(pb_data)

    results: list[TripUpdate] = []

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        tu = entity.trip_update

        if not tu.HasField("trip") or not tu.trip.trip_id:
            continue

        vehicle_id = None
        if tu.HasField("vehicle"):
            vehicle_id = tu.vehicle.id or None

        ts = tu.timestamp if tu.timestamp else None
        if not ts:
            continue
        timestamp = datetime.fromtimestamp(ts, tz=timezone.utc)

        stop_time_updates: list[StopTimeUpdate] = []
        for stu in tu.stop_time_update:
            stop_id = stu.stop_id or None
            if not stop_id:
                continue

            arrival_time = None
            if stu.HasField("arrival") and stu.arrival.time:
                arrival_time = datetime.fromtimestamp(stu.arrival.time, tz=timezone.utc)

            departure_time = None
            if stu.HasField("departure") and stu.departure.time:
                departure_time = datetime.fromtimestamp(stu.departure.time, tz=timezone.utc)

            if arrival_time is None and departure_time is None:
                continue

            stop_time_updates.append(
                StopTimeUpdate(
                    stop_id=stop_id,
                    stop_sequence=None,  # we'll get that from current_stop_times.txt
                    arrival_time=arrival_time,
                    departure_time=departure_time
                )
            )

        if stop_time_updates:
            results.append(
                TripUpdate(
                    agency=agency,
                    trip_id=tu.trip.trip_id,
                    vehicle_id=vehicle_id,
                    timestamp=timestamp,
                    stop_time_updates=stop_time_updates
                )
            )

    return results
