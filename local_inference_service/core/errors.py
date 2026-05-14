class BotValidationError(Exception):
    """Raised when a bot response is invalid."""


class MoveValidationError(Exception):
    """Raised when a MoveEngine response is illegal for the current board."""


class EngineOutputError(Exception):
    """Raised when a MoveEngine stdout line cannot be parsed."""


class EngineProcessError(Exception):
    """Raised when a MoveEngine process cannot produce a valid response."""
