from dataclasses import dataclass

from google.transit import gtfs_realtime_pb2


@dataclass(frozen=True)
class VPItem:
    trip_id: str
    stop_id: str | None
    stop_sequence: int | None
    status: int | None
    vehicle_license_plate: str | None
    rt_timestamp: int | None


def parse_vehicle_positions(pb: bytes) -> tuple[int | None, list[VPItem]]:
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(pb)

    feed_ts = int(feed.header.timestamp) if feed.header.timestamp else None
    out: list[VPItem] = []

    for ent in feed.entity:
        if not ent.HasField("vehicle"):
            continue
        v = ent.vehicle
        if not v.HasField("trip"):
            continue

        trip_id = v.trip.trip_id
        if not trip_id:
            continue

        stop_id = v.stop_id or None
        stop_seq = int(v.current_stop_sequence) if v.HasField("current_stop_sequence") else None
        status = int(v.current_status) if v.HasField("current_status") else None

        plate = None
        if v.HasField("vehicle") and v.vehicle.license_plate:
            plate = v.vehicle.license_plate

        rt_ts = int(v.timestamp) if v.timestamp else feed_ts

        out.append(
            VPItem(
                trip_id=trip_id,
                stop_id=stop_id,
                stop_sequence=stop_seq,
                status=status,
                vehicle_license_plate=plate,
                rt_timestamp=rt_ts,
            )
        )

    return feed_ts, out
