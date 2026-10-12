import structlog

from backend.api.helpers.streamer import stream_message
from backend.core.utils.message_type import MessageType


_logger = structlog.get_logger(__name__)


def log_and_stream(message: str, type: MessageType, **kwargs) -> None:
    if type == MessageType.info:
        _logger.info(message, **kwargs)

    elif type == MessageType.warning:
        _logger.warning(message, **kwargs)

    elif type == MessageType.error:
        _logger.error(message, **kwargs)

    stream_message(message, type)
