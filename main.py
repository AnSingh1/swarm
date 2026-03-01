import asyncio
import os
from dedalus_labs import AsyncDedalus, DedalusRunner
from dedalus_labs.utils.stream import stream_async

# Initialize Laminar
try:
    from lmnr_ai import Laminar
    
    Laminar.initialize({
        "projectApiKey": os.getenv("LMNR_PROJECT_API_KEY"),
        "baseUrl": "http://localhost",
        "httpPort": 8000,
        "grpcPort": 8001,
    })
except ImportError:
    print("Laminar SDK not installed. Skipping initialization.")

async def main():
    client = AsyncDedalus()
    runner = DedalusRunner(client)
    response = await runner.run(
        input="Watch the livestream, capture key moments, and provide real-time updates",
        model=["openai/gpt-5.2", "anthropic/claude-opus-4-6"],
        mcp_servers=["aryanma/browser-use-mcp", "tsion/exa"],
        stream=True,
    )
    await stream_async(response)


if __name__ == "__main__":
    asyncio.run(main())