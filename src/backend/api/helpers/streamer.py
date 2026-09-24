from fastapi import HTTPException
import json
from fastapi.responses import StreamingResponse


def stream_status(message: str):
    return json.dumps({"type": "status", "message": message}) + "\n"


def stream_result(data):
    return json.dumps({"type": "result", "data": data}, allow_nan=False) + "\n"


def stream(func):
    async def run(func):
        try:
            async for result in func:
                yield result

        except HTTPException as error:
            yield json.dumps({
                "type": "error",
                "detail": error.detail,
                "status_code": error.status_code
            }) + "\n"

        except Exception:
            yield json.dumps({
                "type": "error",
                "detail": "Internal server error.",
                "status_code": 500
            }) + "\n"

    return StreamingResponse(
        run(func),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"}
    )