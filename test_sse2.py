import asyncio
from mcp.client.sse import sse_client

async def test_sse():
    print("Testing connection...")
    try:
        # Some versions of mcp require headers
        async with sse_client("https://mcp.data.gouv.fr/mcp", headers={"Accept": "application/json, text/event-stream"}) as streams:
            print("Connected!", streams)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sse())
