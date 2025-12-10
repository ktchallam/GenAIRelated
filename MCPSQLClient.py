# client.py
from fastmcp import Client
import asyncio

async def main():
    # Connect to the server
    async with Client("http://localhost:8000/mcp") as client:
        print("Connected to MCP server!")

        # List all available tools
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        # print("\n")
        # print("CSVdata")

        # csvdata= await client.call_tool("get_client_metadata", {"ClientId":"CL001"})
        # print(csvdata.data)

        # print("\n")
        # print("Set User")
        # set_user = await client.call_tool(
        # "set_user_data",
        # {"name":"Kannan","email":"Varun@example.com"}
        # )

        # print(set_user)

        print("\nGet All User ")
        get_user = await client.call_tool(
            "get_user_data",
            {"name":"All"}  # <── REQUIRED even if empty
        )
        print(get_user.data)
        

        # print("\nGet one User Varun")

        # get_one_user = await client.call_tool(
        #     "get_user_data",
        #     {"name":"Kannan"}   # <── REQUIRED even if empty
        # )
        # print(get_one_user)

        # print("\n Updated user")
        # await client.call_tool(
        #     "update_user",
        #     {"id": 6, "name": "ARKannan", "email": "ARK@example.com"}
        # )
        
        # print("\n details after Updated user")
        # get_one_user = await client.call_tool(
        #     "get_user_data",
        #     {"name":"ARKannan"}   # <── REQUIRED even if empty
        # )
        # print(get_one_user)

        await client.call_tool(
            "delete_user",
            {"id": 6}
        )
        
        print("\nGet All User ")
        get_user = await client.call_tool(
            "get_user_data",
            {"name":"All"}  # <── REQUIRED even if empty
        )
        print(get_user.data)



# Run the client
if __name__ == "__main__":
    asyncio.run(main())
