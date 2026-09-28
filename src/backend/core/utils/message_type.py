from enum import Enum


class MessageType(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"
