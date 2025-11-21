from pathlib import Path

from .models import Mode


class ContextManager:
    """Unified project context for all modes."""

    def __init__(
        self,
        current_mode: Mode = Mode.ROUTER,
        pwd_path: Path = Path.cwd(),
    ):
        """Initialize project context."""
        self._current_mode = current_mode
        self._pwd_path = pwd_path

    @property
    def current_mode(self) -> Mode:
        """Get the current mode."""
        return self._current_mode

    @current_mode.setter
    def current_mode(self, value: Mode) -> None:
        """Set the current mode."""
        self._current_mode = value

    @property
    def pwd_path(self) -> Path:
        """Get the present working directory path."""
        return self._pwd_path
