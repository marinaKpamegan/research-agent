import asyncio
import sys
import os

# Add project root to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from app.services.openrouter_service import OpenRouterService

async def test_completion():
    print("--- Testing create_chat_completion ---")
    service = OpenRouterService()
    messages = [{"role": "user", "content": "What is the capital of France?"}]
    try:
        response = await service.create_chat_completion(messages)
        content = service.extract_response_content(response)
        print(f"Response: {content}")
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

async def test_streaming():
    print("\n--- Testing stream_chat_completion ---")
    service = OpenRouterService()
    messages = [{"role": "user", "content": "Count from 1 to 5."}]
    try:
        print("Chunks: ", end="", flush=True)
        async for chunk in service.stream_chat_completion(messages):
            print(chunk, end="", flush=True)
        print("\nSuccess!")
    except Exception as e:
        print(f"\nError: {e}")

async def main():
    await test_completion()
    await test_streaming()

if __name__ == "__main__":
    asyncio.run(main())
