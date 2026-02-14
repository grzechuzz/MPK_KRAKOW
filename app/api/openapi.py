from typing import Any

import msgspec


def openapi_response(
    struct_type: type[msgspec.Struct], description: str = "Successful Response"
) -> dict[int | str, dict[str, Any]]:
    schema, defs = msgspec.json.schema(struct_type)

    content: dict[str, Any] = {"schema": schema}
    if defs:
        content["schema"]["$defs"] = defs

    return {
        200: {
            "description": description,
            "content": {"application/json": content},
        }
    }
