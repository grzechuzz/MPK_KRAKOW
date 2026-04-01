import json as _json
from collections.abc import Callable
from typing import Any

import msgspec.json as _mjson
from fastapi import FastAPI

from app.api.schemas import (
    ErrorResponse,
    LiveVehicleResponse,
    MaxDelayBetweenStopsResponse,
    PunctualityResponse,
    RouteDelayResponse,
    ShapeResponse,
    TrendResponse,
    TripStopsResponse,
)

_ALL_RESPONSE_TYPES = [
    MaxDelayBetweenStopsResponse,
    RouteDelayResponse,
    PunctualityResponse,
    TrendResponse,
    LiveVehicleResponse,
    ShapeResponse,
    TripStopsResponse,
    ErrorResponse,
]


_EXAMPLE_MAX_DELAY: dict[str, Any] = {
    "line_number": "194",
    "start_date": "2026-02-03",
    "end_date": "2026-02-16",
    "max_delay": [
        {
            "trip_id": "block_675_trip_13_service_2",
            "line_number": "194",
            "vehicle_number": "DR521",
            "from_stop": "Czarnowiejska",
            "to_stop": "AGH / UR",
            "from_sequence": 10,
            "to_sequence": 11,
            "from_planned_time": "2026-02-14 16:49:00",
            "from_event_time": "2026-02-14 16:50:50",
            "to_planned_time": "2026-02-14 16:51:00",
            "to_event_time": "2026-02-14 16:56:43",
            "delay_generated_seconds": 233,
            "headsign": "Os. Pod Fortem",
            "service_date": "2026-02-14",
            "is_estimated": False,
        },
        {
            "trip_id": "block_675_trip_13_service_2",
            "line_number": "194",
            "vehicle_number": "DR521",
            "from_stop": "AGH / UR",
            "to_stop": "Muzeum Narodowe",
            "from_sequence": 11,
            "to_sequence": 12,
            "from_planned_time": "2026-02-14 16:51:00",
            "from_event_time": "2026-02-14 16:56:43",
            "to_planned_time": "2026-02-14 16:53:00",
            "to_event_time": "2026-02-14 17:01:16",
            "delay_generated_seconds": 153,
            "headsign": "Os. Pod Fortem",
            "service_date": "2026-02-14",
            "is_estimated": False,
        },
    ],
    "trips_analyzed": 88,
}

_EXAMPLE_ROUTE_DELAY: dict[str, Any] = {
    "line_number": "304",
    "start_date": "2026-02-01",
    "end_date": "2026-02-16",
    "max_route_delay": [
        {
            "trip_id": "block_781_trip_14_service_2",
            "line_number": "304",
            "vehicle_number": "DE638",
            "first_stop": "Politechnika",
            "last_stop": "Wieliczka Asnyka",
            "first_planned_time": "2026-02-14 16:49:00",
            "first_event_time": "2026-02-14 16:48:31",
            "last_planned_time": "2026-02-14 17:27:00",
            "last_event_time": "2026-02-14 17:44:56",
            "start_delay_seconds": -29,
            "end_delay_seconds": 1076,
            "delay_generated_seconds": 1105,
            "headsign": "Wieliczka Miasto",
            "service_date": "2026-02-14",
            "is_estimated": False,
        },
        {
            "trip_id": "block_780_trip_23_service_2",
            "line_number": "304",
            "vehicle_number": "DE637",
            "first_stop": "Wieliczka Asnyka",
            "last_stop": "Politechnika",
            "first_planned_time": "2026-02-14 17:30:00",
            "first_event_time": "2026-02-14 17:31:58",
            "last_planned_time": "2026-02-14 18:09:00",
            "last_event_time": "2026-02-14 18:29:11",
            "start_delay_seconds": 118,
            "end_delay_seconds": 1211,
            "delay_generated_seconds": 1093,
            "headsign": "Dworzec Główny Zachód",
            "service_date": "2026-02-14",
            "is_estimated": False,
        },
    ],
    "trips_analyzed": 36,
}

_EXAMPLE_PUNCTUALITY: dict[str, Any] = {
    "line_number": "169",
    "start_date": "2026-02-10",
    "end_date": "2026-02-14",
    "total_stops": 280,
    "on_time_count": 63,
    "on_time_percent": 22.5,
    "slightly_delayed_count": 69,
    "slightly_delayed_percent": 24.6,
    "delayed_count": 148,
    "delayed_percent": 52.9,
}

_EXAMPLE_TREND: dict[str, Any] = {
    "line_number": "304",
    "start_date": "2026-02-14",
    "end_date": "2026-02-15",
    "days": [
        {"date": "2026-02-14", "avg_delay_seconds": 415.5, "trips_count": 23},
        {"date": "2026-02-15", "avg_delay_seconds": 218.6, "trips_count": 6},
    ],
}

_EXAMPLE_LIVE_VEHICLES: dict[str, Any] = {
    "count": 5,
    "vehicles": [
        {
            "trip_id": "block_675_trip_13_service_2",
            "license_plate": "DN007",
            "line_number": "179",
            "headsign": "Dworzec Główny Zachód",
            "shape_id": "shape_1234",
            "latitude": 50.0322380065918,
            "longitude": 19.94826316833496,
            "bearing": 90,
            "timestamp": "2026-02-15T17:07:00+00:00",
        },
        {
            "trip_id": "block_622_trip_13_service_3",
            "license_plate": "DN011",
            "line_number": "164",
            "headsign": "Piaski Nowe",
            "shape_id": "shape_9024",
            "latitude": 50.04066848754883,
            "longitude": 19.874757766723633,
            "bearing": 90,
            "timestamp": "2026-02-15T17:07:02+00:00",
        },
        {
            "trip_id": "block_635_trip_11_service_2",
            "license_plate": "DN013",
            "line_number": "503",
            "headsign": "Nowy Bieżanów Południe",
            "shape_id": "shape_8882",
            "latitude": 50.01777648925781,
            "longitude": 19.990068435668945,
            "bearing": 135,
            "timestamp": "2026-02-15T17:06:56+00:00",
        },
        {
            "trip_id": "block_230_trip_4_service_3",
            "license_plate": "DN017",
            "line_number": "179",
            "headsign": "Os. Kurdwanów",
            "shape_id": "shape_7234",
            "latitude": 50.00454330444336,
            "longitude": 19.959930419921875,
            "bearing": 90,
            "timestamp": "2026-02-15T17:06:57+00:00",
        },
        {
            "trip_id": "block_781_trip_14_service_2",
            "license_plate": "DN021",
            "line_number": "503",
            "headsign": "Górka Narodowa P+R",
            "shape_id": "shape_6254",
            "latitude": 50.05740737915039,
            "longitude": 19.926631927490234,
            "bearing": 0,
            "timestamp": "2026-02-15T17:06:53+00:00",
        },
    ],
}

_EXAMPLE_SHAPE: dict[str, Any] = {
    "shape_id": "shape_8882",
    "points": [
        {"latitude": 50.061433, "longitude": 19.936586, "sequence": 1},
        {"latitude": 50.061571, "longitude": 19.937014, "sequence": 2},
        {"latitude": 50.061984, "longitude": 19.938119, "sequence": 3},
    ],
}

_EXAMPLE_TRIP_STOPS: dict[str, Any] = {
    "trip_id": "block_675_trip_13_service_2",
    "stops": [
        {
            "stop_id": "stop_55_7904",
            "stop_name": "Plac Inwalidów",
            "stop_desc": "01",
            "latitude": 50.075130462646484,
            "longitude": 19.906492233276367,
            "sequence": 1,
        },
        {
            "stop_id": "stop_1626_311102",
            "stop_name": "AGH / UR",
            "stop_desc": "02",
            "latitude": 50.09483337402344,
            "longitude": 19.96756935119629,
            "sequence": 2,
        },
        {
            "stop_id": "stop_1654_314104",
            "stop_name": "Muzeum Narodowe",
            "stop_desc": "01",
            "latitude": 50.06626892089844,
            "longitude": 19.99996566772461,
            "sequence": 3,
        },
    ],
}


def _doc(struct_cls: type, example: dict[str, Any]) -> dict[str, Any]:
    return {
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{struct_cls.__name__}"},
                        "example": example,
                    }
                },
            }
        }
    }


DOC_MAX_DELAY = _doc(MaxDelayBetweenStopsResponse, _EXAMPLE_MAX_DELAY)
DOC_ROUTE_DELAY = _doc(RouteDelayResponse, _EXAMPLE_ROUTE_DELAY)
DOC_PUNCTUALITY = _doc(PunctualityResponse, _EXAMPLE_PUNCTUALITY)
DOC_TREND = _doc(TrendResponse, _EXAMPLE_TREND)
DOC_LIVE_VEHICLES = _doc(LiveVehicleResponse, _EXAMPLE_LIVE_VEHICLES)
DOC_SHAPE = _doc(ShapeResponse, _EXAMPLE_SHAPE)
DOC_TRIP_STOPS = _doc(TripStopsResponse, _EXAMPLE_TRIP_STOPS)


def make_openapi_fn(app: FastAPI) -> Callable[[], dict[str, Any]]:
    from fastapi.openapi.utils import get_openapi

    def openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description or "",
            routes=app.routes,
        )

        _, components = _mjson.schema_components(_ALL_RESPONSE_TYPES)

        components_str = _json.dumps(components)
        components_str = components_str.replace('"#/$defs/', '"#/components/schemas/')
        components = _json.loads(components_str)

        schema.setdefault("components", {}).setdefault("schemas", {}).update(components)
        app.openapi_schema = schema
        return schema

    return openapi
