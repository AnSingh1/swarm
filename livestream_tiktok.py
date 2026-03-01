#!/usr/bin/env python3
"""
Livestream TikTok browsing with Browser Use API
- Creates a session with live view URL
- Goes to TikTok
- Clicks "For You" tab
- Scrolls down through videos
"""

import asyncio
import os
from browser_use_sdk import AsyncBrowserUse


async def main():
    # Initialize the Browser Use client with API key
    api_key = os.getenv("BROWSER_USE_API_KEY")
    if not api_key:
        print("❌ Error: BROWSER_USE_API_KEY environment variable not set")
        print("   Get your API key from: https://cloud.browser-use.com/settings?tab=api-keys")
        print("   Then run: export BROWSER_USE_API_KEY='your_key'")
        return
    
    client = AsyncBrowserUse(api_key=api_key)
    
    print("🚀 Creating browser session...")
    
    # Create a session with US proxy (TikTok works best with US)
    session = await client.sessions.create(proxy_country_code="us")
    
    print(f"✅ Session created: {session.id}")
    print(f"📺 Live view URL: {session.live_url}")
    print(f"\n🔗 Open the URL above to watch the browser live!\n")
    
    # Optional: Create a public share link
    try:
        share = await client.sessions.create_share(session.id)
        print(f"🌐 Public share URL: {share.url}")
        print(f"   (This link can be shared with anyone)\n")
    except Exception as e:
        print(f"⚠️  Could not create share link: {e}\n")
    
    print("🎬 Starting TikTok automation...\n")
    
    try:
        # Run the task with streaming to see real-time progress
        task_prompt = """
        Go to TikTok (tiktok.com).
        Click on the "For You" tab if it's not already selected.
        Then scroll down slowly through the videos, pausing briefly to let each video load.
        Scroll down at least 5-10 times to browse through different videos.
        """
        
        async for step in client.run(
            task_prompt,
            session_id=session.id,
            start_url="https://www.tiktok.com",
            max_steps=50,  # Allow enough steps for scrolling
            vision=True,  # Enable vision for better interaction
        ):
            # Print each step as it happens
            print(f"📍 Step {step.number}: {step.next_goal}")
            if step.url:
                print(f"   URL: {step.url}")
            print()
        
        print("✅ Task completed!")
        
        # Keep the session alive for a bit so you can view the final state
        print("\n⏳ Keeping session alive for 30 seconds...")
        print("   (You can still view the live URL)")
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"❌ Error during task: {e}")
    
    finally:
        # Clean up
        print("\n🧹 Cleaning up session...")
        try:
            await client.sessions.stop(session.id)
            await client.sessions.delete(session.id)
            print("✅ Session cleaned up")
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")


if __name__ == "__main__":
    asyncio.run(main())
