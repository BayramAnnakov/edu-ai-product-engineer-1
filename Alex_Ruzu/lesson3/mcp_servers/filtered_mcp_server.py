from agents.mcp.server import MCPServerStdio

class FilteredServer(MCPServerStdio):
    """Expose only a chosen subset of tools from the underlying server."""
    def __init__(self, *args, allowed: set[str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._allowed = set(allowed or [])

    async def list_tools(self):
        tools = await super().list_tools()
        return [t for t in tools if not self._allowed or t.name in self._allowed]

    async def call_tool(self, tool_name: str, arguments: dict | None):
        if self._allowed and tool_name not in self._allowed:
            raise ValueError(f"Tool {tool_name!r} is not whitelisted.")
        return await super().call_tool(tool_name, arguments)
