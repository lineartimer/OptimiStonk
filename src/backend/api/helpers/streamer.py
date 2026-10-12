from anyio import CancelScope
import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from contextvars import ContextVar
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import json

from backend.core.utils.message_type import MessageType


class _MessageStreamer:
    def __init__(self):
        self.queue: asyncio.Queue[str | None] = asyncio.Queue()
        self.loop = asyncio.get_running_loop()
        self.closed = False

    def stream_message(self, message: str | None):
        if not self.closed:
            # For functions run with asyncio.to_thread
            self.loop.call_soon_threadsafe(self.queue.put_nowait, message)

    def close(self):
        self.stream_message(None)
        self.closed = True


class _ResponseStreamer(StreamingResponse):
    async def stream_response(self, send):
        try:
            await super().stream_response(send)
        
        finally:
            with CancelScope(shield=True):
                await self.body_iterator.aclose()


_messages: ContextVar[_MessageStreamer | None] = ContextVar(
    "stream_messages",
    default=None
)


def _emit(event: dict):
    messages = _messages.get()
    if messages is not None and not messages.closed:
        messages.stream_message(json.dumps(event, allow_nan=False) + "\n")


def stream_message(
    message: str,
    message_type: MessageType | None = None,
    new_line: bool = True
):
    _emit({
        "type": "status",
        "message": message,
        "message_type": message_type.value if message_type else MessageType.info,
        "new_line": new_line
    })


def stream_result(data):
    _emit({"type": "result", "data": data})
    return data


def stream(func: Callable[..., Awaitable[object]], *args, **kwargs) -> StreamingResponse:
    async def run():
        messages = _MessageStreamer()

        async def execute():
            token = _messages.set(messages)

            try:
                await func(*args, **kwargs)

            except HTTPException as error:
                _emit({
                    "type": "error",
                    "detail": error.detail,
                    "status_code": error.status_code
                })

            except Exception:
                _emit({
                    "type": "error",
                    "detail": "Internal server error.",
                    "status_code": 500
                })
            
            finally:
                _messages.reset(token)
                messages.close()

        task = asyncio.create_task(execute())

        try:
            while True:
                message = await messages.queue.get()
                if message is None:
                    break
                
                yield message
        
        finally:
            messages.closed = True
            task.cancel()
            with CancelScope(shield=True):
                with suppress(asyncio.CancelledError):
                    await task

    return _ResponseStreamer(
        run(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"}
    )
