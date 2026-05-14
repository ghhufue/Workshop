class MatchServerError(Exception):
    """Base error for match server failures."""


class InvalidMoveError(MatchServerError):
    """Raised when a move violates game or room rules."""


class RoomFullError(MatchServerError):
    """Raised when joining a full room."""


class RoomNotFoundError(MatchServerError):
    """Raised when a room does not exist."""

