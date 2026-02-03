import msgspec

from app.common.redis.schemas import TripUpdateCache, VehicleState

_encoder = msgspec.msgpack.Encoder()

_vehicle_state_decoder = msgspec.msgpack.Decoder(VehicleState)
_trip_update_decoder = msgspec.msgpack.Decoder(TripUpdateCache)


def encode(obj: msgspec.Struct) -> bytes:
    return _encoder.encode(obj)


def decode_vehicle_state(data: bytes) -> VehicleState:
    return _vehicle_state_decoder.decode(data)


def decode_trip_update(data: bytes) -> TripUpdateCache:
    return _trip_update_decoder.decode(data)
