import asyncio
from mcp.client.sse import sse_client

async def test_sse():
    try:
        async with sse_client("https://mcp.data.gouv.fr/mcp") as streams:
            print("Connected!", streams)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test_sse())
