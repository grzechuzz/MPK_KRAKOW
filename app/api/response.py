from typing import Any

import msgspec
from fastapi.responses import JSONResponse


class MsgspecJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return msgspec.json.encode(content)
