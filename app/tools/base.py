from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class BaseTool(ABC):
    name: str
    description: str
    requires_approval: bool = False

    @abstractmethod
    def run(self, payload: dict[str, Any]) -> ToolResult:
        raise NotImplementedError
