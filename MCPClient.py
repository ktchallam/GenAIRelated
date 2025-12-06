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

        # Call the process_data tool
        # result = await client.call_tool(
        #     "process_data",
        #     {"input": "mango"}
        # )
        # print(f"\nResult from process_data: {result}")

        # # Bonus: try the add_numbers tool
        # if any(t.name == "add_numbers" for t in tools):
        #     sum_result = await client.call_tool("add_numbers", {"a": 5, "b": 7})
        #     print(f"5 + 7 = {sum_result}")
        
        print("\n")
        print("CSVdata")

        csvdata= await client.call_tool("get_client_metadata", {"ClientId":"CL001"})
        print(csvdata.data)

# Run the client
if __name__ == "__main__":
    asyncio.run(main())
