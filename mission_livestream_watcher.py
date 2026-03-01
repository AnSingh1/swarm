#!/usr/bin/env python3
"""
Mission Livestream Watcher
Watches for new missions in Convex and starts a TikTok livestream for each one.
Updates the mission with the live URL and session ID.
"""

import asyncio
import os
import sys
import re
from typing import Optional, List
from convex import ConvexClient
from browser_use_sdk import AsyncBrowserUse
from openai import AsyncOpenAI


# Configuration
CONVEX_URL = os.environ.get("CONVEX_URL", "https://flexible-retriever-257.convex.cloud")
BROWSER_USE_API_KEY = os.environ.get("BROWSER_USE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
POLL_INTERVAL = 3  # seconds


async def get_competitor_search_term(mission_prompt: str) -> str:
    """Use OpenAI to generate a competitor search term from the mission prompt."""
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a search-query generator for social media research. "
                        "Given a short mission prompt describing creative content to find (e.g., 'pirate movie trailer'), "
                        "produce a concise TikTok search phrase that will return relevant videos. "
                        "Include specific keywords such as the movie or franchise name, the word 'trailer' or 'official trailer', "
                        "and other helpful modifiers (e.g., 'clip', 'teaser', franchise name). "
                        "Do NOT return only a company or brand name. Return ONLY the search query string on a single line, nothing else."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Create a TikTok search phrase for this mission: {mission_prompt}\n"
                        "Example: for 'pirate movie trailer' return 'disney pirates of the caribbean trailer'"
                    )
                }
            ],
            temperature=0.2,
            max_tokens=80
        )

        search_term = response.choices[0].message.content.strip().strip('"')
        print(f"🤖 AI generated search term: '{search_term}' for mission: '{mission_prompt}'")
        return search_term
        
    except Exception as e:
        print(f"⚠️  Error calling OpenAI: {e}")
        print(f"📝 Falling back to original prompt")
        return mission_prompt


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
            
            # Get the search term using AI
            search_term = await get_competitor_search_term(prompt)
            
            print(f"🎬 Starting TikTok search and analysis...\n")
            print(f"📝 Original Mission: {prompt}")
            print(f"🔍 Searching for: {search_term}\n")
            
            # Phase 1: Search for competitor
            search_task = f"""
            Go to TikTok (tiktok.com). You are already logged in.
            
            Go to the search page and search for: "{search_term}"
            
            Wait for search results to load. Look at the videos displayed.
            """
            
            print("🔍 Phase 1: Searching for competitor content...")
            
            async for step in self.browser_client.run(
                search_task,
                session_id=session.id,
                start_url="https://www.tiktok.com",
                max_steps=20,
                vision=True,
            ):
                pass  # Complete search
            
            print("✅ Search complete\n")
            
            # Phase 2: Click and analyze viral videos
            print("🎥 Phase 2: Collecting viral videos...\n")
            
            discoveries_count = 0
            discovered_screenshots = []  # Store screenshots of discoveries
            
            # Analyze 15-20 videos one at a time
            for video_num in range(1, 21):
                print(f"📹 Video {video_num}/20 - Starting analysis...")
                
                try:
                    # Step 1: Click on a viral video
                    print(f"   🖱️  Finding and clicking video...")
                    click_video_task = f"""
                    You are on the TikTok search results page for "{search_term}".
                    
                    Look at all the videos visible on screen.
                    Find ONE video that:
                    - Has high view count visible (look for "100K", "500K", "1M", etc.)
                    - Has lots of likes (heart icon with big numbers)
                    - You haven't clicked on yet in this session
                    
                    Prioritize videos with the HIGHEST engagement numbers.
                    
                    Click on that ONE video to open it and watch it.
                    DO NOT go to the next video yet - just click this one video.
                    """
                    
                    current_url = None
                    async for step in self.browser_client.run(
                        click_video_task,
                        session_id=session.id,
                        max_steps=15,
                        vision=True,
                    ):
                        if step.url and "tiktok.com/@" in step.url:
                            current_url = step.url
                    
                    if not current_url:
                        print(f"   ⚠️  Could not get video URL, skipping...")
                        continue
                    
                    print(f"   ✅ Opened video: {current_url[:60]}...")
                    
                    # Step 2: Wait for video to load and play
                    print(f"   ⏱️  Waiting for video to load...")
                    await asyncio.sleep(3)  # Give time for video to load and play
                    
                    # Step 3: Take screenshot and use OCR to detect likes
                    print(f"   📸 Taking screenshot for OCR analysis...")
                    screenshot_task = "Take a screenshot of the current page showing the TikTok video and its metrics."
                    screenshot_url = None
                    
                    async for step in self.browser_client.run(
                        screenshot_task,
                        session_id=session.id,
                        max_steps=2,
                        vision=True,
                    ):
                        if hasattr(step, 'screenshot_url') and step.screenshot_url:
                            screenshot_url = step.screenshot_url
                    
                    if not screenshot_url:
                        print(f"   ⚠️  Could not capture screenshot, skipping...")
                        continue
                    
                    print(f"   🔍 Running OCR on screenshot: {screenshot_url}")
                    
                    # Use OpenAI Vision API to read the likes number from screenshot
                    likes_count = 0
                    is_viral = False
                    
                    try:
                        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
                        
                        response = await client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": """Look at this TikTok video screenshot. On the RIGHT side, find the heart icon (like button) and read the number next to it.

The number might be formatted as:
- Plain number like "1949" or "52"
- With K like "1.2K" or "450K"
- With M like "1.5M" or "2M"

Respond with ONLY the number you see next to the heart icon. Just the number, nothing else.

Examples:
- If you see "1949" → respond "1949"
- If you see "52" → respond "52"
- If you see "1.2K" → respond "1.2K"
- If you see "450K" → respond "450K"
"""
                                        },
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": screenshot_url
                                            }
                                        }
                                    ]
                                }
                            ],
                            max_tokens=50
                        )
                        
                        ocr_result = response.choices[0].message.content.strip()
                        print(f"   📊 OCR Result: {ocr_result}")
                        
                        # Parse the likes count
                        patterns = [
                            r'(\d+\.?\d*)[Mm]',  # Matches 1.2M, 5M
                            r'(\d+\.?\d*)[Kk]',  # Matches 1.2K, 450K
                            r'(\d+)',             # Matches plain numbers
                        ]
                        
                        for pattern in patterns:
                            match = re.search(pattern, ocr_result)
                            if match:
                                number_str = match.group(0)
                                
                                # Convert to integer
                                if 'M' in number_str.upper():
                                    likes_count = int(float(number_str.replace('M', '').replace('m', '')) * 1_000_000)
                                elif 'K' in number_str.upper():
                                    likes_count = int(float(number_str.replace('K', '').replace('k', '')) * 1_000)
                                else:
                                    likes_count = int(number_str.replace(',', ''))
                                
                                print(f"   📈 Parsed likes: {likes_count:,}")
                                break
                        
                        # Check if it meets threshold (50+ likes)
                        if likes_count >= 50:
                            is_viral = True
                            print(f"   ✅ VIRAL! ({likes_count:,} likes >= 50)")
                        else:
                            print(f"   ⏭️  Not viral ({likes_count:,} likes < 50)")
                            
                    except Exception as e:
                        print(f"   ⚠️  OCR Error: {e}")
                        print(f"   ⏭️  Skipping this video")
                        is_viral = False
                    
                    # Only log if viral
                    if is_viral and current_url:
                        try:
                            # Log to Convex
                            self.convex_client.mutation(
                                "discoveries:logDiscovery",
                                {
                                    "video_url": current_url,
                                    "thumbnail": "",
                                    "found_by_agent_id": 1,
                                }
                            )
                            discoveries_count += 1
                            
                            # Store screenshot info
                            discovery_info = {
                                "url": current_url,
                                "screenshot": screenshot_url,
                                "metrics": f"{likes_count:,} likes"
                            }
                            discovered_screenshots.append(discovery_info)
                            
                            print(f"   ✨ DISCOVERY #{discoveries_count} LOGGED!")
                            print(f"   🔗 {current_url}")
                            print(f"   💖 {likes_count:,} likes")
                            print(f"   📸 Screenshot: {screenshot_url}")
                        except Exception as e:
                            print(f"   ⚠️  Error logging discovery: {e}")
                    
                    # Step 4: Go back to search results
                    print(f"   ⬅️  Going back to search results...")
                    go_back_task = """
                    Navigate back to the search results page.
                    You can click the back button or use browser navigation.
                    Wait for the search results to load again.
                    """
                    
                    async for step in self.browser_client.run(
                        go_back_task,
                        session_id=session.id,
                        max_steps=8,
                        vision=True,
                    ):
                        pass
                    
                    # Small pause before next video
                    await asyncio.sleep(1)
                    print("")  # Blank line for readability
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    # Try to recover by going back
                    try:
                        async for step in self.browser_client.run(
                            "Go back to the TikTok search results page",
                            session_id=session.id,
                            max_steps=5,
                            vision=True,
                        ):
                            pass
                    except:
                        pass
                    await asyncio.sleep(1)
                    continue
            
            print(f"\n🎉 Analysis complete!")
            print(f"📊 Total discoveries logged: {discoveries_count}/20")
            
            # Display all screenshots at the end
            if discovered_screenshots:
                print(f"\n📸 ========== DISCOVERY SCREENSHOTS ==========\n")
                for i, discovery in enumerate(discovered_screenshots, 1):
                    print(f"Discovery #{i}:")
                    print(f"  🔗 URL: {discovery['url']}")
                    print(f"  📈 Metrics: {discovery['metrics']}")
                    if discovery['screenshot']:
                        print(f"  📸 Screenshot: {discovery['screenshot']}")
                    print()
                print(f"📸 ==========================================\n")
            
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
    
    if not OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Get your API key from: https://platform.openai.com/api-keys")
        print("   Then run: export OPENAI_API_KEY='your_key'")
        sys.exit(1)
    
    # Create and start the watcher
    watcher = MissionLivestreamWatcher()
    await watcher.watch_missions()


if __name__ == "__main__":
    asyncio.run(main())
