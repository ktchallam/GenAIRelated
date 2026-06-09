# Install Node.js 20 via NodeSource
!curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
!apt install -y nodejs

!node -v && npm -v && npx --version

airbnb_server = MCPServerStdio(
    "npx", args=["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"]
)

system_prompt = """
You have access to three tools:
1. get_current_time(params: dict)
2. airbnb_search(params: dict)
3. airbnb_listing_details(params: dict)
When the user asks for listings, first call get_current_time, then airbnb_search, etc.
"""

agent = Agent(
    model=agent_model,
    mcp_servers=[time_server, airbnb_server],
    system_prompt=system_prompt,
)

await run_async("Find a place to stay in Vancouver for next Sunday for 3 nights for 2 adults?")
