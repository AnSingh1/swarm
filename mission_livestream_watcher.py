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


async def get_competitor_search_terms(mission_prompt: str) -> List[str]:
    """Use OpenAI to generate 3 competitor search terms from the mission prompt."""
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a competitive intelligence expert. "
                        "Given a product category, return EXACTLY 3 competitor BRAND/COMPANY NAMES ONLY. "
                        "DO NOT return generic search phrases. DO NOT add words like 'app', 'demo', 'tutorial', 'review'. "
                        "Return ONLY the actual company or product brand names, one per line. "
                        "Examples:\n"
                        "Input: 'AI meeting note taker'\n"
                        "Output:\n"
                        "Otter.ai\n"
                        "Fireflies.ai\n"
                        "Fathom\n\n"
                        "Input: 'project management tool'\n"
                        "Output:\n"
                        "Asana\n"
                        "Monday.com\n"
                        "ClickUp\n\n"
                        "Input: 'video editor'\n"
                        "Output:\n"
                        "CapCut\n"
                        "Adobe Premiere Pro\n"
                        "DaVinci Resolve"
                    )
                },
                {
                    "role": "user",
                    "content": mission_prompt
                }
            ],
            temperature=0.2,
            max_tokens=100
        )

        search_terms_text = response.choices[0].message.content.strip()
        # Split by newlines and clean up
        search_terms = []
        for line in search_terms_text.split('\n'):
            # Remove numbering, bullets, extra whitespace
            cleaned = line.strip().strip('123456789.-)').strip().strip('"').strip(',')
            if cleaned and len(cleaned) > 1:
                search_terms.append(cleaned)
        
        search_terms = search_terms[:3]
        
        # Ensure we have exactly 3 terms
        while len(search_terms) < 3:
            search_terms.append(mission_prompt)
        
        print(f"🤖 AI generated 3 competitor brands for mission: '{mission_prompt}'")
        for i, term in enumerate(search_terms, 1):
            print(f"   {i}. {term}")
        
        return search_terms
        
    except Exception as e:
        print(f"⚠️  Error calling OpenAI: {e}")
        print(f"📝 Falling back to original prompt (3 copies)")
        return [mission_prompt, mission_prompt, mission_prompt]


class MissionLivestreamWatcher:
    def __init__(self):
        self.convex_client = ConvexClient(CONVEX_URL)
        self.browser_client = AsyncBrowserUse(api_key=BROWSER_USE_API_KEY)
        self.last_mission_id: Optional[str] = None
        self.active_sessions = {}
        self.profile_id: Optional[str] = None
        
    async def get_profile_ids(self):
        """Return 3 profile IDs for concurrent sessions."""
        return [
            "06fb7076-4c7d-4264-b53a-e4726c597ac0",
            "31203964-ed13-454f-a27e-0c3054751a8a",
            "8e063dd1-26ab-40ff-bf10-74813b2933e6"
        ]
        
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
        """Start 3 concurrent TikTok livestreams for the given mission."""
        mission_id = mission["_id"]
        prompt = mission["prompt"]
        
        try:
            print(f"🚀 Creating 3 browser sessions for mission {mission_id}...")
            
            # Get 3 search terms and 3 profile IDs
            search_terms = await get_competitor_search_terms(prompt)
            profile_ids = await self.get_profile_ids()
            
            print(f"\n📝 Original Mission: {prompt}\n")
            
            # Create 3 sessions concurrently
            sessions = []
            live_urls = []
            session_tasks = []
            
            for i, (search_term, profile_id) in enumerate(zip(search_terms, profile_ids), 1):
                print(f"\n📺 Session {i}/3:")
                print(f"   🔍 Search term: {search_term}")
                print(f"   🔐 Profile ID: {profile_id[:8]}...")
                
                try:
                    # Create session
                    session = await self.browser_client.sessions.create(
                        proxy_country_code="us",
                        profile_id=profile_id
                    )
                    
                    sessions.append(session)
                    live_urls.append(session.live_url)
                    
                    print(f"   ✅ Session created: {session.id}")
                    print(f"   📺 Live URL: {session.live_url}")
                    
                    # Update agent state in Convex
                    try:
                        self.convex_client.mutation(
                            "agents:updateAgentState",
                            {
                                "agent_id": i,
                                "status": "searching",
                                "current_url": session.live_url,
                                "profile_id": profile_id,
                            }
                        )
                        print(f"   ✅ Agent {i} registered in Convex")
                    except Exception as e:
                        print(f"   ⚠️  Could not register agent: {e}")
                    
                    # Try to create share link
                    try:
                        share = await self.browser_client.sessions.create_share(session.id)
                        print(f"   🌐 Share URL: {share.url}")
                    except Exception as e:
                        print(f"   ⚠️  Could not create share link: {e}")
                    
                except Exception as e:
                    print(f"   ❌ Error creating session {i}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Don't skip - add placeholder so indexing stays correct
                    sessions.append(None)
                    live_urls.append(None)
            
            # Store sessions (filter out None values)
            valid_sessions = [s for s in sessions if s is not None]
            self.active_sessions[mission_id] = valid_sessions
            
            # Filter out None URLs
            valid_live_urls = [url for url in live_urls if url is not None]
            
            # Update mission with all 3 live URLs
            print(f"\n💾 Updating mission with {len(valid_live_urls)} livestream URLs...")
            update_args = {
                "missionId": str(mission_id) if not isinstance(mission_id, str) else mission_id,
                "liveUrl": valid_live_urls[0] if len(valid_live_urls) > 0 else "",
                "sessionId": str(valid_sessions[0].id) if len(valid_sessions) > 0 else "",
            }
            if len(valid_live_urls) > 1:
                update_args["liveUrl2"] = valid_live_urls[1]
                print(f"   📺 Stream 2: {valid_live_urls[1][:50]}...")
            if len(valid_live_urls) > 2:
                update_args["liveUrl3"] = valid_live_urls[2]
                print(f"   📺 Stream 3: {valid_live_urls[2][:50]}...")
            
            print(f"   🔍 Debug - Update args: {update_args.keys()}")
            
            self.convex_client.mutation(
                "missions:updateMissionLivestream",
                update_args
            )
            
            print(f"\n🎬 Starting parallel TikTok analysis on {len(valid_sessions)} sessions...\n")
            
            # Run all sessions concurrently (filter valid sessions)
            analysis_tasks = []
            for i, (session, search_term) in enumerate([(s, st) for s, st in zip(sessions, search_terms) if s is not None], 1):
                task = asyncio.create_task(
                    self.run_single_session_analysis(session, search_term, i)
                )
                analysis_tasks.append(task)
            
            # Wait for all analysis tasks to complete
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Display summary
            total_discoveries = 0
            print(f"\n\n{'='*60}")
            print(f"🎉 ALL SESSIONS COMPLETE!")
            print(f"{'='*60}\n")
            
            for i, result in enumerate(results, 1):
                if isinstance(result, Exception):
                    print(f"Session {i}: ❌ Error - {result}")
                elif isinstance(result, dict):
                    total_discoveries += result.get('discoveries', 0)
                    print(f"Session {i}: ✅ {result.get('discoveries', 0)} discoveries logged")
            
            print(f"\n📊 TOTAL DISCOVERIES ACROSS ALL SESSIONS: {total_discoveries}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"❌ Error starting livestream for mission {mission_id}: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Keep sessions alive for viewing
            print("\n⏳ Keeping sessions alive for 30 seconds...")
            await asyncio.sleep(30)
            
            # Clean up all sessions
            if mission_id in self.active_sessions:
                await self.cleanup_session(mission_id)
    
    async def run_single_session_analysis(self, session, search_term: str, session_num: int):
        """Run analysis on a single TikTok session."""
        try:
            print(f"[Session {session_num}] 🔍 Starting search for: {search_term}")
            
            # Update agent status to searching
            try:
                self.convex_client.mutation(
                    "agents:updateAgentState",
                    {
                        "agent_id": session_num,
                        "status": "searching",
                        "current_url": f"Searching for: {search_term}",
                        "profile_id": (await self.get_profile_ids())[session_num - 1],
                    }
                )
            except Exception as e:
                print(f"[Session {session_num}] ⚠️  Could not update agent status: {e}")
            
            # Phase 1: Search for content
            search_task = f"""
            Go to TikTok (tiktok.com). You are already logged in.
            
            Go to the search page and search for: "{search_term}"
            
            Wait for search results to load. Look at the videos displayed.
            """
            
            async for step in self.browser_client.run(
                search_task,
                session_id=session.id,
                start_url="https://www.tiktok.com",
                max_steps=20,
                vision=True,
            ):
                pass  # Complete search
            
            print(f"[Session {session_num}] ✅ Search complete\n")
            
            # Phase 2: Click and analyze viral videos
            print(f"[Session {session_num}] 🎥 Collecting viral videos...\n")
            
            discoveries_count = 0
            discovered_screenshots = []  # Store screenshots of discoveries
            
            # Analyze 15-20 videos one at a time
            for video_num in range(1, 21):
                print(f"[Session {session_num}] 📹 Video {video_num}/20 - Starting analysis...")
                
                try:
                    # Step 1: Click on a viral video
                    print(f"[Session {session_num}]    🖱️  Finding and clicking video...")
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
                        print(f"[Session {session_num}]    ⚠️  Could not get video URL, skipping...")
                        continue
                    
                    print(f"[Session {session_num}]    ✅ Opened video: {current_url[:60]}...")
                    
                    # Step 2: Wait for video to load and play
                    print(f"[Session {session_num}]    ⏱️  Waiting for video to load...")
                    await asyncio.sleep(3)  # Give time for video to load and play
                    
                    # Step 3: Take screenshot and use OCR to detect likes
                    print(f"[Session {session_num}]    📸 Taking screenshot for OCR analysis...")
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
                        print(f"[Session {session_num}]    ⚠️  Could not capture screenshot, skipping...")
                        continue
                    
                    print(f"[Session {session_num}]    🔍 Running OCR on screenshot...")
                    
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
                        print(f"[Session {session_num}]    📊 OCR Result: {ocr_result}")
                        
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
                                
                                print(f"[Session {session_num}]    📈 Parsed likes: {likes_count:,}")
                                break
                        
                        # Check if it meets threshold (50+ likes)
                        if likes_count >= 50:
                            is_viral = True
                            print(f"[Session {session_num}]    ✅ VIRAL! ({likes_count:,} likes >= 50)")
                        else:
                            print(f"[Session {session_num}]    ⏭️  Not viral ({likes_count:,} likes < 50)")
                            
                    except Exception as e:
                        print(f"[Session {session_num}]    ⚠️  OCR Error: {e}")
                        print(f"[Session {session_num}]    ⏭️  Skipping this video")
                        is_viral = False
                    
                    # Only log if viral
                    if is_viral and current_url:
                        try:
                            # Log to Convex
                            self.convex_client.mutation(
                                "discoveries:logDiscovery",
                                {
                                    "video_url": current_url,
                                    "thumbnail": screenshot_url if screenshot_url else "",
                                    "found_by_agent_id": session_num,
                                }
                            )
                            discoveries_count += 1
                            
                            # Update agent status to found_trend
                            try:
                                self.convex_client.mutation(
                                    "agents:updateAgentState",
                                    {
                                        "agent_id": session_num,
                                        "status": "found_trend",
                                        "current_url": current_url,
                                        "profile_id": (await self.get_profile_ids())[session_num - 1],
                                    }
                                )
                            except Exception as e:
                                print(f"[Session {session_num}]    ⚠️  Could not update agent status: {e}")
                            
                            # Store screenshot info
                            discovery_info = {
                                "url": current_url,
                                "screenshot": screenshot_url,
                                "metrics": f"{likes_count:,} likes"
                            }
                            discovered_screenshots.append(discovery_info)
                            
                            print(f"[Session {session_num}]    ✨ DISCOVERY #{discoveries_count} LOGGED!")
                            print(f"[Session {session_num}]    🔗 {current_url}")
                            print(f"[Session {session_num}]    💖 {likes_count:,} likes")
                            print(f"[Session {session_num}]    📸 Screenshot: {screenshot_url}")
                        except Exception as e:
                            print(f"[Session {session_num}]    ⚠️  Error logging discovery: {e}")
                    
                    # Step 4: Go back to search results
                    print(f"[Session {session_num}]    ⬅️  Going back to search results...")
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
                    
                except Exception as e:
                    print(f"[Session {session_num}]    ❌ Error: {e}")
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
            
            print(f"\n[Session {session_num}] 🎉 Analysis complete!")
            print(f"[Session {session_num}] 📊 Discoveries logged: {discoveries_count}/20\n")
            
            # Update agent status to idle
            try:
                self.convex_client.mutation(
                    "agents:updateAgentState",
                    {
                        "agent_id": session_num,
                        "status": "idle",
                        "current_url": "Analysis complete",
                        "profile_id": (await self.get_profile_ids())[session_num - 1],
                    }
                )
            except Exception as e:
                print(f"[Session {session_num}] ⚠️  Could not update agent status: {e}")
            
            return {"discoveries": discoveries_count, "screenshots": discovered_screenshots}
            
        except Exception as e:
            print(f"[Session {session_num}] ❌ Error in session: {e}")
            import traceback
            traceback.print_exc()
            return {"discoveries": 0, "screenshots": []}
    
    async def cleanup_session(self, mission_id):
        """Clean up all sessions for a mission."""
        if mission_id not in self.active_sessions:
            return
        
        sessions = self.active_sessions[mission_id]
        
        # Handle both single session (old format) and multiple sessions (new format)
        if not isinstance(sessions, list):
            sessions = [sessions]
        
        try:
            print(f"\n🧹 Cleaning up {len(sessions)} session(s) for mission {mission_id}...")
            for i, session in enumerate(sessions, 1):
                try:
                    await self.browser_client.sessions.stop(session.id)
                    await self.browser_client.sessions.delete(session.id)
                    print(f"   ✅ Session {i}/{len(sessions)} cleaned up")
                except Exception as e:
                    print(f"   ⚠️  Error cleaning up session {i}: {e}")
            print(f"✅ All sessions cleaned up for mission {mission_id}")
        except Exception as e:
            print(f"⚠️  Error cleaning up sessions: {e}")
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
