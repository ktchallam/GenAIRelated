!pip install -q mcp-server-time

from pydantic_ai.mcp import MCPServerStdio

time_server = MCPServerStdio(
    "python",
    args=[
        "-m", "mcp_server_time",
        "--local-timezone=America/New_York",
    ],
)

agent = Agent(
    model=agent_model,
    mcp_servers=[time_server],
    system_prompt = (
        "You are a helpful agent and you have access to this tool:\n"
        "   get_current_time(params: dict)\n"
        "When the user asks for the current date or time, call get_current_time.\n"
    )
)

await run_async("What’s the date today?")
