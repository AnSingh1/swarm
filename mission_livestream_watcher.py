#!/usr/bin/env python3
"""
Mission Livestream Watcher
Watches for new missions in Convex and starts a TikTok livestream for each one.
Updates the mission with the live URL and session ID.
"""

import asyncio
import os
import sys
from typing import Optional
from convex import ConvexClient
from browser_use_sdk import AsyncBrowserUse


# Configuration
CONVEX_URL = os.environ.get("CONVEX_URL", "https://flexible-retriever-257.convex.cloud")
BROWSER_USE_API_KEY = os.environ.get("BROWSER_USE_API_KEY")
POLL_INTERVAL = 3  # seconds


class MissionLivestreamWatcher:
    def __init__(self):
        self.convex_client = ConvexClient(CONVEX_URL)
        self.browser_client = AsyncBrowserUse(api_key=BROWSER_USE_API_KEY)
        self.last_mission_id: Optional[str] = None
        self.active_sessions = {}
        
    async def watch_missions(self):
        """Continuously watch for new missions and start livestreams."""
        print("🔍 Starting mission livestream watcher...")
        print(f"📡 Connected to Convex: {CONVEX_URL}\n")
        
        while True:
            try:
                # Get the latest mission
                mission = self.convex_client.query("missions:getLatestMission")
                
                if mission and mission["_id"] != self.last_mission_id:
                    # New mission detected!
                    print(f"\n🆕 New mission detected: {mission['_id']}")
                    print(f"📝 Prompt: {mission['prompt']}\n")
                    
                    # Start the livestream in the background
                    asyncio.create_task(self.start_livestream(mission))
                    
                    # Update the last mission ID
                    self.last_mission_id = mission["_id"]
                
                # Wait before checking again
                await asyncio.sleep(POLL_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n⏹️  Stopping watcher...")
                await self.cleanup_all_sessions()
                break
            except Exception as e:
                print(f"❌ Error in watch loop: {e}")
                await asyncio.sleep(POLL_INTERVAL)
    
    async def start_livestream(self, mission):
        """Start a TikTok livestream for the given mission."""
        mission_id = mission["_id"]
        prompt = mission["prompt"]
        
        try:
            print(f"🚀 Creating browser session for mission {mission_id}...")
            
            # Create a session with US proxy
            session = await self.browser_client.sessions.create(proxy_country_code="us")
            
            print(f"✅ Session created: {session.id}")
            print(f"📺 Live view URL: {session.live_url}")
            
            # Store the session
            self.active_sessions[mission_id] = session
            
            # Try to create a public share link
            share_url = None
            try:
                share = await self.browser_client.sessions.create_share(session.id)
                share_url = share.url
                print(f"🌐 Public share URL: {share_url}")
            except Exception as e:
                print(f"⚠️  Could not create share link: {e}")
            
            # Update the mission with livestream URLs
            print(f"💾 Updating mission with livestream URLs...")
            # Ensure mission_id is passed as a string for Convex ID type
            update_args = {
                "missionId": str(mission_id) if not isinstance(mission_id, str) else mission_id,
                "liveUrl": session.live_url,
                "sessionId": str(session.id),
            }
            if share_url:
                update_args["shareUrl"] = share_url
            
            self.convex_client.mutation(
                "missions:updateMissionLivestream",
                update_args
            )
            
            print(f"🎬 Starting TikTok automation...\n")
            
            # Run the TikTok browsing task
            task_prompt = """
            Go to TikTok (tiktok.com).
            Click on the "For You" tab if it's not already selected.
            Then scroll down slowly through the videos, pausing briefly to let each video load.
            Keep scrolling and browsing indefinitely until instructed to stop.
            """
            
            # Start the task in streaming mode
            step_count = 0
            async for step in self.browser_client.run(
                task_prompt,
                session_id=session.id,
                start_url="https://www.tiktok.com",
                max_steps=200,  # Allow many steps for continuous scrolling
                vision=True,  # Enable vision for better interaction
            ):
                step_count += 1
                if step_count % 5 == 0:  # Print every 5th step to reduce noise
                    print(f"📍 Step {step.number}: {step.next_goal}")
                    if step.url:
                        print(f"   URL: {step.url[:80]}...")
            
            print(f"✅ Task completed for mission {mission_id}")
            
        except Exception as e:
            print(f"❌ Error starting livestream for mission {mission_id}: {e}")
        
        finally:
            # Clean up the session after the task completes
            if mission_id in self.active_sessions:
                await self.cleanup_session(mission_id)
    
    async def cleanup_session(self, mission_id):
        """Clean up a specific session."""
        if mission_id not in self.active_sessions:
            return
        
        session = self.active_sessions[mission_id]
        try:
            print(f"\n🧹 Cleaning up session for mission {mission_id}...")
            await self.browser_client.sessions.stop(session.id)
            await self.browser_client.sessions.delete(session.id)
            print(f"✅ Session cleaned up for mission {mission_id}")
        except Exception as e:
            print(f"⚠️  Error cleaning up session: {e}")
        finally:
            del self.active_sessions[mission_id]
    
    async def cleanup_all_sessions(self):
        """Clean up all active sessions."""
        for mission_id in list(self.active_sessions.keys()):
            await self.cleanup_session(mission_id)


async def main():
    # Check for required environment variables
    if not BROWSER_USE_API_KEY:
        print("❌ Error: BROWSER_USE_API_KEY environment variable not set")
        print("   Get your API key from: https://cloud.browser-use.com/settings?tab=api-keys")
        print("   Then run: export BROWSER_USE_API_KEY='your_key'")
        sys.exit(1)
    
    # Create and start the watcher
    watcher = MissionLivestreamWatcher()
    await watcher.watch_missions()


if __name__ == "__main__":
    asyncio.run(main())
