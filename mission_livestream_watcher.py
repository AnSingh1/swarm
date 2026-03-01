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
import time
import json
from typing import Optional, List
from convex import ConvexClient
from browser_use_sdk import AsyncBrowserUse
from openai import AsyncOpenAI
import dotenv

loaded = dotenv.load_dotenv()


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
        
        # SWARM INTELLIGENCE ADDITIONS
        self.agent_energy = {}  # agent_id -> energy level
        self.agent_tasks = {}  # agent_id -> asyncio Task
        self.discovered_competitors = set()  # Track discovered competitor names
        self.original_search_terms = []  # The 3 original competitors
        self.swarm_manager_task: Optional[asyncio.Task] = None
        self.swarm_running = False
        
    async def get_profile_ids(self):
        """Return 3 profile IDs for concurrent sessions."""
        return [
            "06fb7076-4c7d-4264-b53a-e4726c597ac0",
            "31203964-ed13-454f-a27e-0c3054751a8a",
            "8e063dd1-26ab-40ff-bf10-74813b2933e6"
        ]
    
    async def extract_keywords_from_content(self, content_description: str) -> str:
        """
        Use LLM to extract 2-3 defining keywords from discovered content.
        This feeds the Blackboard for exploitation by other agents.
        """
        try:
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract 2-3 key defining words from this content description. Return only the keywords separated by commas, lowercase, no extra text."
                    },
                    {
                        "role": "user",
                        "content": content_description
                    }
                ],
                max_tokens=30,
                temperature=0.3
            )
            keywords = response.choices[0].message.content.strip()
            return keywords
        except Exception as e:
            print(f"   ⚠️  Keyword extraction failed: {e}")
            return "trending, viral, popular"  # fallback
    
    def log(self, agent_id: int, message: str, log_type: str, metadata: dict = None):
        """
        Helper to log agent activity to Convex.
        
        Args:
            agent_id: The agent ID (1-9, or 0 for swarm manager)
            message: The log message
            log_type: One of: search, analysis, likes, discovery, energy_gain, energy_loss, task_swap, status, error
            metadata: Optional dict with extra data
        """
        try:
            self.convex_client.mutation(
                "logs:addLog",
                {
                    "agent_id": agent_id,
                    "message": message,
                    "type": log_type,
                    "timestamp": time.time(),
                    "metadata": json.dumps(metadata) if metadata else None,
                }
            )
        except Exception as e:
            # Don't let logging failures break the agent
            print(f"[Log Error] Agent {agent_id}: {e}")
    
    async def swarm_manager(self):
        """
        **BLACKBOARD ARCHITECTURE - SWARM MANAGER**
        
        This background task polls Convex every 10 seconds to:
        1. Check for weak agents (energy <= 0)
        2. Query the Blackboard (discoveries table) for latest successful find
        3. Reassign weak agents to exploit that discovery
        4. Check for stop commands from the UI
        """
        print(f"\n🧠 SWARM MANAGER STARTED - Monitoring agent energy every 10s")
        
        while self.swarm_running:
            try:
                await asyncio.sleep(10)
                
                # CHECK FOR STOP COMMAND
                try:
                    pending_commands = self.convex_client.query("control:getPendingCommands")
                    for cmd in pending_commands:
                        if cmd["command"] == "stop_all":
                            print(f"\n{'='*70}")
                            print(f"🛑 STOP COMMAND RECEIVED FROM UI")
                            print(f"{'='*70}")
                            
                            # Mark command as processing
                            self.convex_client.mutation("control:markCommandProcessing", {"commandId": cmd["_id"]})
                            
                            # Stop the swarm
                            self.swarm_running = False
                            
                            # Log the stop
                            self.log(0, "Stop command received - shutting down all agents", "status")
                            
                            # Mark command as completed
                            self.convex_client.mutation("control:markCommandCompleted", {"commandId": cmd["_id"]})
                            
                            print("✅ Graceful shutdown initiated...")
                            return
                except Exception as e:
                    # Don't let command checking break the swarm manager
                    pass
                
                # Find weak agents
                weak_agents = [agent_id for agent_id, energy in self.agent_energy.items() if energy <= 0]
                
                # EMERGENCY REFILL: If ALL agents are depleted, refill everyone
                if weak_agents and len(weak_agents) == len(self.agent_energy):
                    print(f"\n{'='*70}")
                    print(f"🚨 EMERGENCY: ALL {len(weak_agents)} AGENTS DEPLETED!")
                    print(f"💊 REFILLING ALL AGENTS TO 100 ENERGY")
                    print(f"{'='*70}")
                    
                    for agent_id in weak_agents:
                        self.agent_energy[agent_id] = 100
                        self.log(agent_id, "Emergency refill! Energy: 0 → 100", "energy_refill", {
                            "old": 0,
                            "new": 100,
                            "reason": "all_depleted"
                        })
                        
                        # Update agent status
                        try:
                            self.convex_client.mutation(
                                "agents:updateAgentState",
                                {
                                    "agent_id": agent_id,
                                    "status": "searching",
                                    "current_url": "Refilled and ready",
                                    "energy": 100
                                }
                            )
                        except:
                            pass
                    
                    print(f"✅ All agents refilled and reset to searching status\n")
                    continue
                
                if not weak_agents:
                    continue
                
                print(f"\n{'='*70}")
                print(f"⚠️  SWARM MANAGER: Found {len(weak_agents)} weak agent(s)")
                
                # Query the Blackboard for the latest discovery
                try:
                    latest_discovery = self.convex_client.query("discoveries:getLatestDiscovery")
                except:
                    latest_discovery = None
                
                if not latest_discovery:
                    print(f"📋 Blackboard is empty - no discoveries to exploit yet")
                    continue
                
                # Extract exploitation context from the discovery
                keywords = latest_discovery.get("keywords", "trending content")
                finder_agent_id = latest_discovery.get("found_by_agent_id")
                
                print(f"📋 BLACKBOARD EXPLOITATION:")
                print(f"   Latest discovery by Agent {finder_agent_id}")
                print(f"   Keywords: {keywords}")
                
                # Reassign weak agents to exploit this discovery
                for agent_id in weak_agents:
                    if agent_id not in self.active_sessions or agent_id not in self.agent_tasks:
                        continue
                    
                    # Determine platform
                    if agent_id <= 3:
                        platform = "TikTok"
                    elif agent_id <= 6:
                        platform = "YouTube"
                    else:
                        platform = "DuckDuckGo"
                    
                    print(f"   🔄 Reassigning Agent {agent_id} ({platform}) to exploit: {keywords}")
                    
                    # LOG: Task swap
                    self.log(agent_id, f"Task swap! Exploiting: {keywords}", "task_swap", {"keywords": keywords})
                    
                    # Reset energy
                    self.agent_energy[agent_id] = 100
                    
                    # Update status in Convex
                    try:
                        self.convex_client.mutation(
                            "agents:updateAgentState",
                            {
                                "agent_id": agent_id,
                                "status": "exploiting",
                                "current_url": f"Exploiting: {keywords}",
                                "energy": 100
                            }
                        )
                    except:
                        pass
                    
                    # LOG: Energy gain
                    self.log(agent_id, f"Energy: 0 → 100 (+100)", "energy_gain", {"old": 0, "new": 100})
                    
                    print(f"      ✅ Energy reset to 100, now exploiting discovery")
                
                print(f"{'='*70}\n")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Swarm Manager error: {e}")
                continue
        
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
            
            # SWARM INTELLIGENCE: Store original competitors and initialize energy
            self.original_search_terms = search_terms
            self.discovered_competitors = set(term.lower() for term in search_terms)
            print(f"\n🎯 Original Competitors (will not be re-discovered): {', '.join(search_terms)}")
            
            # Initialize all agent energies to 100
            for i in range(1, 10):
                self.agent_energy[i] = 100
            
            # Start swarm manager
            self.swarm_running = True
            self.swarm_manager_task = asyncio.create_task(self.swarm_manager())
            
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
                                "energy": 100,
                            }
                        )
                        print(f"   ✅ Agent {i} registered in Convex (Energy: 100)")
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
            
            # Store TikTok sessions (filter out None values)
            valid_sessions = [s for s in sessions if s is not None]
            
            # Filter out None URLs
            valid_live_urls = [url for url in live_urls if url is not None]
            
            # Now create 3 YouTube Shorts sessions (agents 4, 5, and 6) using all 3 search terms
            print(f"\n📺 Creating 3 YouTube Shorts sessions (no profiles)...")
            youtube_sessions = []
            youtube_live_urls = []
            
            # Use all 3 search terms for YouTube
            youtube_search_terms = search_terms  # All 3 terms
            
            for i, search_term in enumerate(youtube_search_terms, 1):
                agent_num = i + 3  # Agents 4, 5, and 6
                print(f"\n🎥 YouTube Session {i}/3 (Agent {agent_num}):")
                print(f"   🔍 Search term: {search_term}")
                print(f"   🚫 No profile (anonymous)")
                
                try:
                    # Create session WITHOUT profile_id for YouTube
                    session = await self.browser_client.sessions.create(
                        proxy_country_code="us"
                        # No profile_id parameter
                    )
                    
                    youtube_sessions.append(session)
                    youtube_live_urls.append(session.live_url)
                    
                    print(f"   ✅ Session created: {session.id}")
                    print(f"   📺 Live URL: {session.live_url}")
                    
                    # Update agent state in Convex
                    try:
                        self.convex_client.mutation(
                            "agents:updateAgentState",
                            {
                                "agent_id": agent_num,
                                "status": "searching",
                                "current_url": session.live_url,
                                "profile_id": "none",  # No profile for YouTube
                                "energy": 100,
                            }
                        )
                        print(f"   ✅ Agent {agent_num} registered in Convex (Energy: 100)")
                    except Exception as e:
                        print(f"   ⚠️  Could not register agent: {e}")
                    
                except Exception as e:
                    print(f"   ❌ Error creating YouTube session {i}: {e}")
                    import traceback
                    traceback.print_exc()
                    youtube_sessions.append(None)
                    youtube_live_urls.append(None)
            
            # Combine all sessions
            all_valid_sessions = valid_sessions + [s for s in youtube_sessions if s is not None]
            
            # Now create 3 DuckDuckGo search agents (agents 7, 8, and 9) using all 3 search terms
            print(f"\n🔍 Creating 3 DuckDuckGo search agents (no profiles)...")
            ddg_sessions = []
            ddg_live_urls = []
            
            # Use all 3 search terms for DuckDuckGo
            ddg_search_terms = search_terms  # All 3 terms
            
            for i, search_term in enumerate(ddg_search_terms, 1):
                agent_num = i + 6  # Agents 7, 8, and 9
                print(f"\n🦆 DuckDuckGo Session {i}/3 (Agent {agent_num}):")
                print(f"   🔍 Search term: {search_term}")
                print(f"   🚫 No profile (anonymous)")
                
                try:
                    # Create session WITHOUT profile_id for DuckDuckGo
                    session = await self.browser_client.sessions.create(
                        proxy_country_code="us"
                        # No profile_id parameter
                    )
                    
                    ddg_sessions.append(session)
                    ddg_live_urls.append(session.live_url)
                    
                    print(f"   ✅ Session created: {session.id}")
                    print(f"   📺 Live URL: {session.live_url}")
                    
                    # Update agent state in Convex
                    try:
                        self.convex_client.mutation(
                            "agents:updateAgentState",
                            {
                                "agent_id": agent_num,
                                "status": "searching",
                                "current_url": session.live_url,
                                "profile_id": "none",  # No profile for DuckDuckGo
                                "energy": 100,
                            }
                        )
                        print(f"   ✅ Agent {agent_num} registered in Convex (Energy: 100)")
                    except Exception as e:
                        print(f"   ⚠️  Could not register agent: {e}")
                    
                except Exception as e:
                    print(f"   ❌ Error creating DuckDuckGo session {i}: {e}")
                    import traceback
                    traceback.print_exc()
                    ddg_sessions.append(None)
                    ddg_live_urls.append(None)
            
            # Combine all sessions
            all_valid_sessions = all_valid_sessions + [s for s in ddg_sessions if s is not None]
            self.active_sessions[mission_id] = all_valid_sessions
            
            # Filter YouTube URLs
            valid_youtube_urls = [url for url in youtube_live_urls if url is not None]
            
            # Filter DuckDuckGo URLs
            valid_ddg_urls = [url for url in ddg_live_urls if url is not None]
            
            # Update mission with all 9 live URLs (3 TikTok + 3 YouTube + 3 DuckDuckGo)
            print(f"\n💾 Updating mission with {len(valid_live_urls) + len(valid_youtube_urls) + len(valid_ddg_urls)} livestream URLs...")
            update_args = {
                "missionId": str(mission_id) if not isinstance(mission_id, str) else mission_id,
                "liveUrl": valid_live_urls[0] if len(valid_live_urls) > 0 else "",
                "sessionId": str(valid_sessions[0].id) if len(valid_sessions) > 0 else "",
            }
            if len(valid_live_urls) > 1:
                update_args["liveUrl2"] = valid_live_urls[1]
                print(f"   📺 TikTok 2: {valid_live_urls[1][:50]}...")
            if len(valid_live_urls) > 2:
                update_args["liveUrl3"] = valid_live_urls[2]
                print(f"   📺 TikTok 3: {valid_live_urls[2][:50]}...")
            if len(valid_youtube_urls) > 0:
                update_args["liveUrl4"] = valid_youtube_urls[0]
                print(f"   🎥 YouTube 1: {valid_youtube_urls[0][:50]}...")
            if len(valid_youtube_urls) > 1:
                update_args["liveUrl5"] = valid_youtube_urls[1]
                print(f"   🎥 YouTube 2: {valid_youtube_urls[1][:50]}...")
            if len(valid_youtube_urls) > 2:
                update_args["liveUrl6"] = valid_youtube_urls[2]
                print(f"   🎥 YouTube 3: {valid_youtube_urls[2][:50]}...")
            if len(valid_ddg_urls) > 0:
                update_args["liveUrl7"] = valid_ddg_urls[0]
                print(f"   🦆 DuckDuckGo 1: {valid_ddg_urls[0][:50]}...")
            if len(valid_ddg_urls) > 1:
                update_args["liveUrl8"] = valid_ddg_urls[1]
                print(f"   🦆 DuckDuckGo 2: {valid_ddg_urls[1][:50]}...")
            if len(valid_ddg_urls) > 2:
                update_args["liveUrl9"] = valid_ddg_urls[2]
                print(f"   🦆 DuckDuckGo 3: {valid_ddg_urls[2][:50]}...")
            
            print(f"   🔍 Debug - Update args: {update_args.keys()}")
            
            self.convex_client.mutation(
                "missions:updateMissionLivestream",
                update_args
            )
            
            print(f"\n🎬 Starting parallel analysis: {len(valid_sessions)} TikTok + {len([s for s in youtube_sessions if s is not None])} YouTube + {len([s for s in ddg_sessions if s is not None])} DuckDuckGo...\n")
            
            # Run all sessions concurrently
            analysis_tasks = []
            
            # TikTok sessions (agents 1, 2, 3)
            for i, (session, search_term) in enumerate([(s, st) for s, st in zip(sessions, search_terms) if s is not None], 1):
                task = asyncio.create_task(
                    self.run_single_session_analysis(session, search_term, i)
                )
                analysis_tasks.append(task)
            
            # YouTube sessions (agents 4, 5, 6)
            for i, (session, search_term) in enumerate([(s, st) for s, st in zip(youtube_sessions, youtube_search_terms) if s is not None], 1):
                agent_num = i + 3
                task = asyncio.create_task(
                    self.run_youtube_shorts_analysis(session, search_term, agent_num)
                )
                analysis_tasks.append(task)
            
            # DuckDuckGo sessions (agents 7, 8, 9)
            for i, (session, search_term) in enumerate([(s, st) for s, st in zip(ddg_sessions, ddg_search_terms) if s is not None], 1):
                agent_num = i + 6
                task = asyncio.create_task(
                    self.run_duckduckgo_analysis(session, search_term, agent_num)
                )
                analysis_tasks.append(task)
            
            # Wait for all analysis tasks to complete
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Display summary
            total_discoveries = 0
            print(f"\n\n{'='*60}")
            print(f"🎉 ALL SESSIONS COMPLETE!")
            print(f"{'='*60}\n")
            
            num_tiktok = len([s for s in sessions if s is not None])
            num_youtube = len([s for s in youtube_sessions if s is not None])
            num_ddg = len([s for s in ddg_sessions if s is not None])
            
            for i, result in enumerate(results, 1):
                if i <= num_tiktok:
                    platform = "TikTok"
                elif i <= num_tiktok + num_youtube:
                    platform = "YouTube"
                else:
                    platform = "DuckDuckGo"
                    
                if isinstance(result, Exception):
                    print(f"Session {i} ({platform}): ❌ Error - {result}")
                elif isinstance(result, dict):
                    total_discoveries += result.get('discoveries', 0)
                    print(f"Session {i} ({platform}): ✅ {result.get('discoveries', 0)} discoveries logged")
            
            print(f"\n📊 TOTAL DISCOVERIES: {total_discoveries}")
            print(f"   - TikTok Sessions: {num_tiktok}")
            print(f"   - YouTube Sessions: {num_youtube}")
            print(f"   - DuckDuckGo Sessions: {num_ddg}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"❌ Error starting livestream for mission {mission_id}: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Stop swarm manager
            self.swarm_running = False
            if self.swarm_manager_task and not self.swarm_manager_task.done():
                self.swarm_manager_task.cancel()
                try:
                    await self.swarm_manager_task
                except asyncio.CancelledError:
                    pass
            print("\n🧠 Swarm manager stopped")
            
            # Check if this was a user-requested stop (skip the 30s wait)
            try:
                pending_commands = self.convex_client.query("control:getPendingCommands")
                user_stopped = any(cmd.get("command") == "stop_all" for cmd in pending_commands)
            except:
                user_stopped = False
            
            if not user_stopped:
                # Keep sessions alive for viewing (only if not user-stopped)
                print("\n⏳ Keeping sessions alive for 30 seconds...")
                await asyncio.sleep(30)
            else:
                print("\n🛑 User requested stop - cleaning up immediately...")
            
            # Clean up all sessions
            if mission_id in self.active_sessions:
                await self.cleanup_session(mission_id)
    
    async def run_single_session_analysis(self, session, search_term: str, session_num: int):
        """Run analysis on a single TikTok session."""
        try:
            print(f"[Session {session_num}] 🔍 Starting search for: {search_term}")
            
            # LOG: Search started
            self.log(session_num, f"Searching for: {search_term}", "search", {"platform": "TikTok", "term": search_term})
            
            # Update agent status to searching
            try:
                self.convex_client.mutation(
                    "agents:updateAgentState",
                    {
                        "agent_id": session_num,
                        "status": "searching",
                        "current_url": f"Searching for: {search_term}",
                        "profile_id": (await self.get_profile_ids())[session_num - 1],
                        "energy": 100,
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
            
            # Analyze 40 videos one at a time (extended for more startup time)
            for video_num in range(1, 41):
                # Check if stop was requested
                if not self.swarm_running:
                    print(f"[Session {session_num}] 🛑 Stop requested, ending analysis early")
                    break
                
                print(f"[Session {session_num}] 📹 Video {video_num}/40 - Starting analysis...")
                
                # LOG: Analysis progress
                self.log(session_num, f"Analyzing video {video_num}/40", "analysis", {"video_num": video_num, "total": 40})
                
                try:
                    # Step 1: Click on first video OR scroll to next
                    if video_num == 1:
                        print(f"[Session {session_num}]    🖱️  Finding and clicking first viral video...")
                        click_video_task = f"""
                        You are on the TikTok search results page for "{search_term}".
                        
                        Look at all the videos visible on screen.
                        Find ONE video that:
                        - Has high view count visible (look for "100K", "500K", "1M", etc.)
                        - Has lots of likes (heart icon with big numbers)
                        
                        Click on that ONE video to open it in the TikTok video player.
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
                    else:
                        # Scroll/swipe to next video in the feed
                        print(f"[Session {session_num}]    ⬇️  Scrolling to next video...")
                        scroll_task = """
                        You are watching a TikTok video in the player.
                        Swipe down or scroll down to go to the next video in the feed.
                        Wait for the next video to load and start playing.
                        """
                        
                        current_url = None
                        async for step in self.browser_client.run(
                            scroll_task,
                            session_id=session.id,
                            max_steps=8,
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
                                
                                # LOG: Likes found
                                self.log(session_num, f"Found {likes_count:,} likes", "likes", {"likes": likes_count, "video_num": video_num})
                                
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
                            # Extract keywords for Blackboard
                            keywords = await self.extract_keywords_from_content(f"TikTok video about {search_term} with {likes_count} likes")
                            
                            # Log to Convex with keywords
                            self.convex_client.mutation(
                                "discoveries:logDiscovery",
                                {
                                    "video_url": current_url,
                                    "thumbnail": screenshot_url if screenshot_url else "",
                                    "found_by_agent_id": session_num,
                                    "keywords": keywords,
                                }
                            )
                            discoveries_count += 1
                            
                            # SWARM INTELLIGENCE: Success! Reset energy to 100
                            old_energy = self.agent_energy.get(session_num, 100)
                            self.agent_energy[session_num] = 100
                            
                            # LOG: Discovery made
                            self.log(session_num, f"Discovery! {keywords} ({likes_count:,} likes)", "discovery", {
                                "keywords": keywords,
                                "likes": likes_count,
                                "url": current_url
                            })
                            
                            # LOG: Energy gain (if energy was not already 100)
                            if old_energy != 100:
                                diff = 100 - old_energy
                                self.log(session_num, f"Energy: {old_energy} → 100 (+{diff})", "energy_gain", {
                                    "old": old_energy,
                                    "new": 100,
                                    "diff": diff
                                })
                            
                            # Update agent status to found_trend with energy reset
                            try:
                                self.convex_client.mutation(
                                    "agents:updateAgentState",
                                    {
                                        "agent_id": session_num,
                                        "status": "found_trend",
                                        "current_url": current_url,
                                        "profile_id": (await self.get_profile_ids())[session_num - 1],
                                        "energy": 100,
                                    }
                                )
                                print(f"[Session {session_num}]    ⚡ Energy: {old_energy} → 100 (SUCCESS)")
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
                            print(f"[Session {session_num}]    🔑 Keywords: {keywords}")
                            print(f"[Session {session_num}]    🔗 {current_url}")
                            print(f"[Session {session_num}]    💖 {likes_count:,} likes")
                            print(f"[Session {session_num}]    📸 Screenshot: {screenshot_url}")
                        except Exception as e:
                            print(f"[Session {session_num}]    ⚠️  Error logging discovery: {e}")
                    
                    # Small pause before scrolling to next video
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"[Session {session_num}]    ❌ Error: {e}")
                    await asyncio.sleep(1)
                    # Continue to next video even if there was an error
                    continue
            
            print(f"\n[Session {session_num}] 🎉 Analysis complete!")
            print(f"[Session {session_num}] 📊 Discoveries logged: {discoveries_count}/40\n")
            
            # SWARM INTELLIGENCE: If no discoveries, deduct energy
            if discoveries_count == 0:
                old_energy = self.agent_energy.get(session_num, 100)
                new_energy = max(0, old_energy - 30)
                self.agent_energy[session_num] = new_energy
                print(f"[Session {session_num}] ⚡ Energy deducted: {old_energy} → {new_energy} (NO DISCOVERIES)")
                
                # LOG: Energy loss
                self.log(session_num, f"Energy: {old_energy} → {new_energy} (-30)", "energy_loss", {
                    "old": old_energy,
                    "new": new_energy,
                    "reason": "no_discoveries"
                })
                
                status = "weak" if new_energy <= 0 else "idle"
            else:
                status = "idle"
            
            # Update agent status to idle
            try:
                self.convex_client.mutation(
                    "agents:updateAgentState",
                    {
                        "agent_id": session_num,
                        "status": status,
                        "current_url": "Analysis complete",
                        "profile_id": (await self.get_profile_ids())[session_num - 1],
                        "energy": self.agent_energy.get(session_num, 100),
                    }
                )
            except Exception as e:
                print(f"[Session {session_num}] ⚠️  Could not update agent status: {e}")
            
            return {"discoveries": discoveries_count, "screenshots": discovered_screenshots}
            
        except Exception as e:
            print(f"[Session {session_num}] ❌ Error in session: {e}")
            import traceback
            traceback.print_exc()
            
            # SWARM INTELLIGENCE: Error = deduct energy
            old_energy = self.agent_energy.get(session_num, 100)
            new_energy = max(0, old_energy - 30)
            self.agent_energy[session_num] = new_energy
            print(f"[Session {session_num}] ⚡ Energy deducted: {old_energy} → {new_energy} (ERROR)")
            
            # LOG: Error and energy loss
            self.log(session_num, f"Error: {str(e)[:50]}", "error", {"error": str(e)})
            self.log(session_num, f"Energy: {old_energy} → {new_energy} (-30)", "energy_loss", {
                "old": old_energy,
                "new": new_energy,
                "reason": "error"
            })
            
            return {"discoveries": 0, "screenshots": []}
    
    async def run_youtube_shorts_analysis(self, session, search_term: str, session_num: int):
        """Run analysis on a single YouTube Shorts session."""
        try:
            print(f"[YT Session {session_num}] 🔍 Starting search for: {search_term}")
            
            # LOG: Search started
            self.log(session_num, f"Searching for: {search_term}", "search", {"platform": "YouTube", "term": search_term})
            
            # Update agent status to searching
            try:
                self.convex_client.mutation(
                    "agents:updateAgentState",
                    {
                        "agent_id": session_num,
                        "status": "searching",
                        "current_url": f"Searching YouTube for: {search_term}",
                        "profile_id": "none",
                        "energy": 100,
                    }
                )
            except Exception as e:
                print(f"[YT Session {session_num}] ⚠️  Could not update agent status: {e}")
            
            # Phase 1: Search for content on YouTube
            search_task = f"""
            Go to YouTube (youtube.com).
            
            Use the search bar to search for: "{search_term}"
            
            Wait for search results to load. Look for the Shorts section or Shorts videos.
            """
            
            async for step in self.browser_client.run(
                search_task,
                session_id=session.id,
                start_url="https://www.youtube.com",
                max_steps=20,
                vision=True,
            ):
                pass  # Complete search
            
            print(f"[YT Session {session_num}] ✅ Search complete\n")
            
            # Phase 2: Click on first Short and analyze
            print(f"[YT Session {session_num}] 🎥 Analyzing YouTube Shorts...\n")
            
            discoveries_count = 0
            discovered_screenshots = []
            
            # Analyze 40 Shorts one at a time (extended for more startup time)
            for video_num in range(1, 41):
                # Check if stop was requested
                if not self.swarm_running:
                    print(f"[YT Session {session_num}] 🛑 Stop requested, ending analysis early")
                    break
                
                print(f"[YT Session {session_num}] 📹 Short {video_num}/40 - Starting analysis...")
                
                # LOG: Analysis progress
                self.log(session_num, f"Analyzing Short {video_num}/40", "analysis", {"video_num": video_num, "total": 40})
                
                try:
                    # Step 1: Click on a Short (or navigate to next if already in Shorts player)
                    if video_num == 1:
                        print(f"[YT Session {session_num}]    🖱️  Finding and clicking first Short...")
                        click_short_task = f"""
                        You are on YouTube search results for "{search_term}".
                        
                        Look for the Shorts section or find a Short video (vertical video format).
                        Click on the FIRST Short you see to open the Shorts player.
                        """
                        
                        async for step in self.browser_client.run(
                            click_short_task,
                            session_id=session.id,
                            max_steps=15,
                            vision=True,
                        ):
                            pass
                    else:
                        # Navigate to next Short using keyboard or swipe
                        print(f"[YT Session {session_num}]    ⬇️  Moving to next Short...")
                        next_short_task = """
                        You are in the YouTube Shorts player.
                        Swipe down or scroll down to go to the next Short video.
                        Wait for the next Short to load.
                        """
                        
                        async for step in self.browser_client.run(
                            next_short_task,
                            session_id=session.id,
                            max_steps=8,
                            vision=True,
                        ):
                            pass
                    
                    # Step 2: Wait for Short to load
                    print(f"[YT Session {session_num}]    ⏱️  Waiting for Short to load...")
                    await asyncio.sleep(3)
                    
                    # Step 3: Get current URL
                    current_url = None
                    get_url_task = "What is the current URL?"
                    async for step in self.browser_client.run(
                        get_url_task,
                        session_id=session.id,
                        max_steps=2,
                        vision=True,
                    ):
                        if step.url:
                            current_url = step.url
                    
                    if not current_url:
                        print(f"[YT Session {session_num}]    ⚠️  Could not get video URL, skipping...")
                        continue
                    
                    print(f"[YT Session {session_num}]    ✅ Current Short: {current_url[:60]}...")
                    
                    # Step 4: Take screenshot and use OCR to detect likes
                    print(f"[YT Session {session_num}]    📸 Taking screenshot for OCR analysis...")
                    screenshot_task = "Take a screenshot of the current YouTube Short showing the video and its metrics."
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
                        print(f"[YT Session {session_num}]    ⚠️  Could not capture screenshot, skipping...")
                        continue
                    
                    print(f"[YT Session {session_num}]    🔍 Running OCR on screenshot...")
                    
                    # Use OpenAI Vision API to read the likes number
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
                                            "text": """Look at this YouTube Short screenshot. Find the thumbs up (like) icon and read the number next to it.

The number might be formatted as:
- Plain number like "1.5K" or "234"
- With K like "12K" or "450K"
- With M like "1.5M" or "2M"

Respond with ONLY the number you see next to the thumbs up icon. Just the number, nothing else.

Examples:
- If you see "1.5K" → respond "1.5K"
- If you see "234" → respond "234"
- If you see "12K" → respond "12K"
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
                        print(f"[YT Session {session_num}]    📊 OCR Result: {ocr_result}")
                        
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
                                
                                print(f"[YT Session {session_num}]    📈 Parsed likes: {likes_count:,}")
                                
                                # LOG: Likes found
                                self.log(session_num, f"Found {likes_count:,} likes", "likes", {"likes": likes_count, "video_num": video_num})
                                
                                break
                        
                        # Check if it meets threshold (50+ likes)
                        if likes_count >= 50:
                            is_viral = True
                            print(f"[YT Session {session_num}]    ✅ VIRAL! ({likes_count:,} likes >= 50)")
                        else:
                            print(f"[YT Session {session_num}]    ⏭️  Not viral ({likes_count:,} likes < 50)")
                            
                    except Exception as e:
                        print(f"[YT Session {session_num}]    ⚠️  OCR Error: {e}")
                        print(f"[YT Session {session_num}]    ⏭️  Skipping this Short")
                        is_viral = False
                    
                    # Only log if viral
                    if is_viral and current_url:
                        try:
                            # Extract keywords for Blackboard
                            keywords = await self.extract_keywords_from_content(f"YouTube short about {search_term} with {likes_count} likes")
                            
                            # Log to Convex with keywords
                            self.convex_client.mutation(
                                "discoveries:logDiscovery",
                                {
                                    "video_url": current_url,
                                    "thumbnail": screenshot_url if screenshot_url else "",
                                    "found_by_agent_id": session_num,
                                    "keywords": keywords,
                                }
                            )
                            discoveries_count += 1
                            
                            # SWARM INTELLIGENCE: Success! Reset energy to 100
                            old_energy = self.agent_energy.get(session_num, 100)
                            self.agent_energy[session_num] = 100
                            
                            # LOG: Discovery made
                            self.log(session_num, f"Discovery! {keywords} ({likes_count:,} likes)", "discovery", {
                                "keywords": keywords,
                                "likes": likes_count,
                                "url": current_url
                            })
                            
                            # LOG: Energy gain (if energy was not already 100)
                            if old_energy != 100:
                                diff = 100 - old_energy
                                self.log(session_num, f"Energy: {old_energy} → 100 (+{diff})", "energy_gain", {
                                    "old": old_energy,
                                    "new": 100,
                                    "diff": diff
                                })
                            
                            # Update agent status to found_trend with energy reset
                            try:
                                self.convex_client.mutation(
                                    "agents:updateAgentState",
                                    {
                                        "agent_id": session_num,
                                        "status": "found_trend",
                                        "current_url": current_url,
                                        "profile_id": "none",
                                        "energy": 100,
                                    }
                                )
                                print(f"[YT Session {session_num}]    ⚡ Energy: {old_energy} → 100 (SUCCESS)")
                            except Exception as e:
                                print(f"[YT Session {session_num}]    ⚠️  Could not update agent status: {e}")
                            
                            # Store screenshot info
                            discovery_info = {
                                "url": current_url,
                                "screenshot": screenshot_url,
                                "metrics": f"{likes_count:,} likes"
                            }
                            discovered_screenshots.append(discovery_info)
                            
                            print(f"[YT Session {session_num}]    ✨ DISCOVERY #{discoveries_count} LOGGED!")
                            print(f"[YT Session {session_num}]    🔑 Keywords: {keywords}")
                            print(f"[YT Session {session_num}]    🔗 {current_url}")
                            print(f"[YT Session {session_num}]    💖 {likes_count:,} likes")
                            print(f"[YT Session {session_num}]    📸 Screenshot: {screenshot_url}")
                        except Exception as e:
                            print(f"[YT Session {session_num}]    ⚠️  Error logging discovery: {e}")
                    
                    # Small pause before next Short
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"[YT Session {session_num}]    ❌ Error: {e}")
                    await asyncio.sleep(1)
                    continue
            
            print(f"\n[YT Session {session_num}] 🎉 Analysis complete!")
            print(f"[YT Session {session_num}] 📊 Discoveries logged: {discoveries_count}/40\n")
            
            # SWARM INTELLIGENCE: If no discoveries, deduct energy
            if discoveries_count == 0:
                old_energy = self.agent_energy.get(session_num, 100)
                new_energy = max(0, old_energy - 30)
                self.agent_energy[session_num] = new_energy
                print(f"[YT Session {session_num}] ⚡ Energy deducted: {old_energy} → {new_energy} (NO DISCOVERIES)")
                
                # LOG: Energy loss
                self.log(session_num, f"Energy: {old_energy} → {new_energy} (-30)", "energy_loss", {
                    "old": old_energy,
                    "new": new_energy,
                    "reason": "no_discoveries"
                })
                
                status = "weak" if new_energy <= 0 else "idle"
            else:
                status = "idle"
            
            # Update agent status to idle
            try:
                self.convex_client.mutation(
                    "agents:updateAgentState",
                    {
                        "agent_id": session_num,
                        "status": status,
                        "current_url": "Analysis complete",
                        "profile_id": "none",
                        "energy": self.agent_energy.get(session_num, 100),
                    }
                )
            except Exception as e:
                print(f"[YT Session {session_num}] ⚠️  Could not update agent status: {e}")
            
            return {"discoveries": discoveries_count, "screenshots": discovered_screenshots}
            
        except Exception as e:
            print(f"[YT Session {session_num}] ❌ Error in YouTube session: {e}")
            import traceback
            traceback.print_exc()
            
            # SWARM INTELLIGENCE: Error = deduct energy
            old_energy = self.agent_energy.get(session_num, 100)
            new_energy = max(0, old_energy - 30)
            self.agent_energy[session_num] = new_energy
            print(f"[YT Session {session_num}] ⚡ Energy deducted: {old_energy} → {new_energy} (ERROR)")
            
            # LOG: Error and energy loss
            self.log(session_num, f"Error: {str(e)[:50]}", "error", {"error": str(e)})
            self.log(session_num, f"Energy: {old_energy} → {new_energy} (-30)", "energy_loss", {
                "old": old_energy,
                "new": new_energy,
                "reason": "error"
            })
            
            return {"discoveries": 0, "screenshots": []}
    
    async def run_duckduckgo_analysis(self, session, search_term: str, session_num: int):
        """Run web search and extraction analysis on DuckDuckGo."""
        try:
            print(f"[DDG Session {session_num}] 🔍 Starting search for: {search_term}")
            
            # LOG: Search started
            self.log(session_num, f"Searching for: {search_term}", "search", {"platform": "DuckDuckGo", "term": search_term})
            
            # Update agent status to searching
            try:
                self.convex_client.mutation(
                    "agents:updateAgentState",
                    {
                        "agent_id": session_num,
                        "status": "searching",
                        "current_url": f"Searching DuckDuckGo for: {search_term}",
                        "profile_id": "none",
                        "energy": 100,
                    }
                )
            except Exception as e:
                print(f"[DDG Session {session_num}] ⚠️  Could not update agent status: {e}")
            
            # Phase 1: Search on DuckDuckGo
            search_task = f"""
            Go to DuckDuckGo (duckduckgo.com).
            
            Use the search box to search for: "{search_term}"
            
            Wait for search results to load. Look at the top search results.
            """
            
            async for step in self.browser_client.run(
                search_task,
                session_id=session.id,
                start_url="https://www.duckduckgo.com",
                max_steps=15,
                vision=True,
            ):
                pass  # Complete search
            
            print(f"[DDG Session {session_num}] ✅ Search complete\n")
            
            # Phase 2: Visit top search results and extract information
            print(f"[DDG Session {session_num}] 🌐 Visiting and extracting from websites...\n")
            
            discoveries_count = 0
            discovered_pages = []
            
            # Visit 20 top search results (extended for more startup time)
            for result_num in range(1, 21):
                # Check if stop was requested
                if not self.swarm_running:
                    print(f"[DDG Session {session_num}] 🛑 Stop requested, ending analysis early")
                    break
                
                print(f"[DDG Session {session_num}] 🔗 Result {result_num}/20 - Analyzing...")
                
                try:
                    # Step 1: Click on a search result
                    if result_num == 1:
                        print(f"[DDG Session {session_num}]    🖱️  Clicking on first search result...")
                        click_result_task = f"""
                        You are on DuckDuckGo search results for "{search_term}".
                        
                        Find the FIRST organic search result (not an ad).
                        Click on it to visit the website.
                        """
                        
                        async for step in self.browser_client.run(
                            click_result_task,
                            session_id=session.id,
                            max_steps=10,
                            vision=True,
                        ):
                            pass
                    else:
                        # Go back to search results and click next result
                        print(f"[DDG Session {session_num}]    ⬅️  Going back to search results...")
                        back_task = """
                        Navigate back to the DuckDuckGo search results page.
                        You can click the back button or use browser navigation.
                        """
                        
                        async for step in self.browser_client.run(
                            back_task,
                            session_id=session.id,
                            max_steps=8,
                            vision=True,
                        ):
                            pass
                        
                        await asyncio.sleep(1)
                        
                        print(f"[DDG Session {session_num}]    🖱️  Clicking on next result...")
                        click_next_task = f"""
                        You are on DuckDuckGo search results.
                        
                        Find the next organic search result that you haven't clicked yet.
                        Click on it to visit the website.
                        """
                        
                        async for step in self.browser_client.run(
                            click_next_task,
                            session_id=session.id,
                            max_steps=10,
                            vision=True,
                        ):
                            pass
                    
                    # Step 2: Wait for page to load
                    print(f"[DDG Session {session_num}]    ⏱️  Waiting for page to load...")
                    await asyncio.sleep(3)
                    
                    # Step 3: Get current URL
                    current_url = None
                    get_url_task = "What is the current URL?"
                    async for step in self.browser_client.run(
                        get_url_task,
                        session_id=session.id,
                        max_steps=2,
                        vision=True,
                    ):
                        if step.url:
                            current_url = step.url
                    
                    if not current_url or "duckduckgo.com" in current_url:
                        print(f"[DDG Session {session_num}]    ⚠️  Still on search page or no URL, skipping...")
                        continue
                    
                    print(f"[DDG Session {session_num}]    ✅ Visiting: {current_url[:60]}...")
                    
                    # Step 4: Take screenshot and extract key information
                    print(f"[DDG Session {session_num}]    📸 Taking screenshot...")
                    screenshot_task = "Take a screenshot of the current page."
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
                        print(f"[DDG Session {session_num}]    ⚠️  Could not capture screenshot, skipping...")
                        continue
                    
                    print(f"[DDG Session {session_num}]    🔍 Extracting information from page...")
                    
                    # Use OpenAI Vision API to extract key information
                    page_info = ""
                    is_relevant = False
                    
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
                                            "text": f"""Look at this webpage screenshot for "{search_term}".

Extract key information about this company/product:
1. What is the main product or service?
2. What are the key features or benefits mentioned?
3. Is there any pricing information visible?
4. Any social proof (testimonials, user count, ratings)?

Respond in a concise 2-3 sentence summary. If the page is relevant to "{search_term}", start with "RELEVANT:". If not relevant or it's just a generic list/directory, start with "NOT RELEVANT:".
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
                            max_tokens=200
                        )
                        
                        extraction_result = response.choices[0].message.content.strip()
                        print(f"[DDG Session {session_num}]    📊 Extraction: {extraction_result[:100]}...")
                        
                        # Check if relevant
                        if extraction_result.startswith("RELEVANT:"):
                            is_relevant = True
                            page_info = extraction_result.replace("RELEVANT:", "").strip()
                            print(f"[DDG Session {session_num}]    ✅ RELEVANT PAGE!")
                        else:
                            print(f"[DDG Session {session_num}]    ⏭️  Not relevant, skipping")
                            
                    except Exception as e:
                        print(f"[DDG Session {session_num}]    ⚠️  Extraction Error: {e}")
                        print(f"[DDG Session {session_num}]    ⏭️  Skipping this page")
                        is_relevant = False
                    
                    # Only log if relevant
                    if is_relevant and current_url:
                        # SWARM INTELLIGENCE: Extract competitor name and check if new
                        try:
                            # Extract company/product name from URL or page info
                            import re
                            # Try to extract domain name as competitor identifier
                            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', current_url)
                            competitor_name = domain_match.group(1).lower() if domain_match else current_url
                            
                            # Also try to extract from page_info
                            company_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', page_info)
                            if company_names and len(company_names[0]) > 2:
                                competitor_name = company_names[0].lower()
                            
                            # Check if this competitor is already discovered (original 3 or previously found)
                            if competitor_name in self.discovered_competitors:
                                print(f"[DDG Session {session_num}]    ⏭️  Already discovered: {competitor_name}, skipping")
                                continue
                            
                            # NEW COMPETITOR! Add to discovered set
                            self.discovered_competitors.add(competitor_name)
                            print(f"[DDG Session {session_num}]    🆕 NEW COMPETITOR: {competitor_name}")
                            
                            # Extract keywords for Blackboard
                            keywords = await self.extract_keywords_from_content(page_info)
                            
                            # Log to Convex with keywords
                            self.convex_client.mutation(
                                "discoveries:logDiscovery",
                                {
                                    "video_url": current_url,
                                    "thumbnail": screenshot_url if screenshot_url else "",
                                    "found_by_agent_id": session_num,
                                    "keywords": keywords,
                                }
                            )
                            discoveries_count += 1
                            
                            # SWARM INTELLIGENCE: Success! Reset energy to 100
                            old_energy = self.agent_energy.get(session_num, 100)
                            self.agent_energy[session_num] = 100
                            
                            # LOG: Discovery made (new competitor)
                            self.log(session_num, f"New competitor! {competitor_name} - {keywords}", "discovery", {
                                "keywords": keywords,
                                "competitor": competitor_name,
                                "url": current_url
                            })
                            
                            # LOG: Energy gain (if energy was not already 100)
                            if old_energy != 100:
                                diff = 100 - old_energy
                                self.log(session_num, f"Energy: {old_energy} → 100 (+{diff})", "energy_gain", {
                                    "old": old_energy,
                                    "new": 100,
                                    "diff": diff
                                })
                            
                            # Update agent status to found_trend with energy reset
                            try:
                                self.convex_client.mutation(
                                    "agents:updateAgentState",
                                    {
                                        "agent_id": session_num,
                                        "status": "found_trend",
                                        "current_url": current_url,
                                        "profile_id": "none",
                                        "energy": 100,
                                    }
                                )
                                print(f"[DDG Session {session_num}]    ⚡ Energy: {old_energy} → 100 (SUCCESS)")
                            except Exception as e:
                                print(f"[DDG Session {session_num}]    ⚠️  Could not update agent status: {e}")
                            
                            # Store page info
                            discovery_info = {
                                "url": current_url,
                                "screenshot": screenshot_url,
                                "info": page_info
                            }
                            discovered_pages.append(discovery_info)
                            
                            print(f"[DDG Session {session_num}]    ✨ DISCOVERY #{discoveries_count} LOGGED!")
                            print(f"[DDG Session {session_num}]    🔑 Keywords: {keywords}")
                            print(f"[DDG Session {session_num}]    🔗 {current_url}")
                            print(f"[DDG Session {session_num}]    📝 {page_info[:80]}...")
                            print(f"[DDG Session {session_num}]    📸 Screenshot: {screenshot_url}")
                        except Exception as e:
                            print(f"[DDG Session {session_num}]    ⚠️  Error logging discovery: {e}")
                    
                    # Small pause before next result
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"[DDG Session {session_num}]    ❌ Error: {e}")
                    await asyncio.sleep(1)
                    continue
            
            print(f"\n[DDG Session {session_num}] 🎉 Analysis complete!")
            print(f"[DDG Session {session_num}] 📊 Discoveries logged: {discoveries_count}/20\n")
            
            # SWARM INTELLIGENCE: If no discoveries, deduct energy
            if discoveries_count == 0:
                old_energy = self.agent_energy.get(session_num, 100)
                new_energy = max(0, old_energy - 30)
                self.agent_energy[session_num] = new_energy
                print(f"[DDG Session {session_num}] ⚡ Energy deducted: {old_energy} → {new_energy} (NO DISCOVERIES)")
                
                # LOG: Energy loss
                self.log(session_num, f"Energy: {old_energy} → {new_energy} (-30)", "energy_loss", {
                    "old": old_energy,
                    "new": new_energy,
                    "reason": "no_discoveries"
                })
                
                status = "weak" if new_energy <= 0 else "idle"
            else:
                status = "idle"
            
            # Update agent status to idle
            try:
                self.convex_client.mutation(
                    "agents:updateAgentState",
                    {
                        "agent_id": session_num,
                        "status": status,
                        "current_url": "Analysis complete",
                        "profile_id": "none",
                        "energy": self.agent_energy.get(session_num, 100),
                    }
                )
            except Exception as e:
                print(f"[DDG Session {session_num}] ⚠️  Could not update agent status: {e}")
            
            return {"discoveries": discoveries_count, "pages": discovered_pages}
            
        except Exception as e:
            print(f"[DDG Session {session_num}] ❌ Error in DuckDuckGo session: {e}")
            import traceback
            traceback.print_exc()
            
            # SWARM INTELLIGENCE: Error = deduct energy
            old_energy = self.agent_energy.get(session_num, 100)
            new_energy = max(0, old_energy - 30)
            self.agent_energy[session_num] = new_energy
            print(f"[DDG Session {session_num}] ⚡ Energy deducted: {old_energy} → {new_energy} (ERROR)")
            
            # LOG: Error and energy loss
            self.log(session_num, f"Error: {str(e)[:50]}", "error", {"error": str(e)})
            self.log(session_num, f"Energy: {old_energy} → {new_energy} (-30)", "energy_loss", {
                "old": old_energy,
                "new": new_energy,
                "reason": "error"
            })
            
            return {"discoveries": 0, "pages": []}
    
    
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
