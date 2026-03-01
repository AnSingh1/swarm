#!/usr/bin/env python3
"""
Mission Livestream Watcher
Watches for new missions in Convex and starts a TikTok livestream for each one.
Updates the mission with the live URL and session ID.
"""

import asyncio
import os
import sys
from typing import Optional, List
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
        self.profile_id: Optional[str] = None
        
    async def get_profile_id(self):
        return "06fb7076-4c7d-4264-b53a-e4726c597ac0"
        
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
            
            # Get the 'pro' profile ID (already logged into TikTok)
            profile_id = await self.get_profile_id()
            
            # Create a session with US proxy and the 'pro' profile
            session = await self.browser_client.sessions.create(
                proxy_country_code="us",
                profile_id=profile_id
            )
            
            print(f"✅ Session created: {session.id}")
            print(f"🔐 Using profile 'pro' (already logged into TikTok)")
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
            
            print(f"🎬 Starting TikTok search and analysis...\n")
            print(f"📝 Mission: {prompt}\n")
            
            # Search task (no login needed - already logged in via profile)
            search_task = f"""
            Go to TikTok (tiktok.com). You are already logged in.
            
            Go to the search page and search for: "{prompt}"
            
            Wait for search results to load, then scroll down slowly 2-3 times.
            """
            
            print("🔍 Starting search...")
            step_count = 0
            
            async for step in self.browser_client.run(
                search_task,
                session_id=session.id,
                start_url="https://www.tiktok.com",
                max_steps=30,
                vision=True,
            ):
                step_count += 1
                if step_count % 3 == 0:
                    print(f"   Step {step.number}: {step.next_goal[:80]}...")
            
            print("✅ Search complete\n")
            
            # Phase 2: Scroll and analyze videos
            print("🔍 Analyzing videos...")
            
            # Run multiple analysis cycles
            for cycle in range(5):  # 5 cycles of analysis
                print(f"\n📊 Analysis cycle {cycle + 1}/5")
                
                # Scroll and collect videos
                scroll_task = """
                Scroll down through the TikTok search results slowly.
                Scroll down 3-5 times, pausing between scrolls to let videos load.
                """
                
                async for step in self.browser_client.run(
                    scroll_task,
                    session_id=session.id,
                    max_steps=10,
                    vision=True,
                ):
                    pass  # Just scroll
                
                # Now analyze what's on screen
                analyze_task = f"""
                Look at the TikTok videos currently visible on the screen.
                
                For each video you can see:
                1. Read the video title/caption
                2. Look at the thumbnail
                3. Check the creator name and account
                4. Evaluate if it matches this mission: "{prompt}"
                
                For ANY video that is relevant to "{prompt}", extract:
                - The full video URL (TikTok share link)
                - The thumbnail image URL
                - The video title/caption
                - A brief explanation of why it's relevant
                
                Return a list of ALL relevant videos you find.
                Be thorough but selective - only include videos that truly match the mission.
                """
                
                try:
                    # Use structured output to get video discoveries
                    result = await self.browser_client.run(
                        analyze_task,
                        session_id=session.id,
                        max_steps=15,
                        vision=True,
                    )
                    
                    # The result should contain information we can parse
                    if hasattr(result, 'output') and result.output:
                        output_str = str(result.output)
                        print(f"   Analysis output: {output_str[:200]}...")
                        
                        # Look for TikTok URLs in the output
                        import re
                        tiktok_urls = re.findall(r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+', output_str)
                        
                        for video_url in tiktok_urls:
                            try:
                                # Log discovery to Convex
                                self.convex_client.mutation(
                                    "discoveries:logDiscovery",
                                    {
                                        "video_url": video_url,
                                        "thumbnail": "",  # Will be empty for now
                                        "found_by_agent_id": 1,
                                    }
                                )
                                print(f"   ✨ Logged discovery: {video_url}")
                            except Exception as e:
                                print(f"   ⚠️  Error logging discovery: {e}")
                
                except Exception as e:
                    print(f"   ⚠️  Error in analysis: {e}")
                
                # Small delay between cycles
                await asyncio.sleep(2)
            
            print(f"\n✅ Task completed for mission {mission_id}")
            
        except Exception as e:
            print(f"❌ Error starting livestream for mission {mission_id}: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Keep session alive for viewing
            print("\n⏳ Keeping session alive for 30 seconds...")
            await asyncio.sleep(30)
            
            # Clean up the session
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
