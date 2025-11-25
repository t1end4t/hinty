from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List
from baml_py import BamlSyncStream


@dataclass
class AgentResponse:
    """Unified response structure for all agents."""

    response: str | BamlSyncStream[str, str] | None = None
    metadata: Dict[str, Any] | None = None
    actions: List[str] | None = None
    thinking: str | None = None


@dataclass
class ToolResult:
    """Result of a tool function call."""

    success: bool
    output: Any | None = None
    error: str | None = None


class Mode(Enum):
    SMART = "smart"
    CHATGPT = "chatgpt"
    CODER = "code"
    RESEARCHER = "research"
    WRITER = "write"
    SECOND_BRAIN = "second-brain"

    @classmethod
    def from_string(cls, value: str) -> "Mode":
        """Convert string to Mode enum."""
        for mode in cls:
            if mode.value == value.lower():
                return mode
        raise ValueError(f"Unknown mode: {value}")

    @classmethod
    def get_values(cls) -> List[str]:
        """Get all mode values as strings."""
        return [mode.value for mode in cls]
