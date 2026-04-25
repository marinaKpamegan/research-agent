import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://mcp.data.gouv.fr/mcp",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            follow_redirects=True
        )
        print("Status", resp.status_code)
        print("Text", repr(resp.text))

asyncio.run(main())
