from app.tools.base import BaseTool, ToolResult
from app.tools.conversation_tools import ConversationSummaryTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def run(self, name: str, payload: dict) -> ToolResult:
        tool = self.get(name)

        if tool is None:
            return ToolResult(
                success=False,
                error=f"Tool not found: {name}",
            )

        return tool.run(payload)

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
            }
            for tool in self._tools.values()
        ]


tool_registry = ToolRegistry()
tool_registry.register(ConversationSummaryTool())
