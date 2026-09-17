from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Tool:
    """An LLM-callable capability, described as an OpenAI-style function schema."""

    name: str
    description: str
    parameters: dict[str, Any]
    run: Callable[..., Awaitable[str]]

    def to_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
