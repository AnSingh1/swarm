#!/usr/bin/env python3
"""
Swarm Intelligence Orchestrator with Blackboard Architecture
============================================================

This orchestrator manages 9 browser agents using a risk/reward system:
- Agents start with 100 energy
- Failed tasks deduct 30 energy
- Successful discoveries reset energy to 100
- Weak agents (energy <= 0) are reassigned based on discoveries from other agents

**Blackboard Architecture**: All agents share discoveries via Convex database.
When one agent finds something viral, weak agents are redirected to exploit that discovery.

**Agents**:
- 1-3: TikTok (with profiles)
- 4-6: YouTube Shorts (no profiles) 
- 7-9: DuckDuckGo Web Search (no profiles)
"""

import asyncio
import os
import sys
import re
from typing import Optional, List, Dict, Set
from convex import ConvexClient
from browser_use_sdk import AsyncBrowserUse
from openai import AsyncOpenAI

import dotenv
dotenv.load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================
CONVEX_URL = os.environ.get("CONVEX_URL", "https://flexible-retriever-257.convex.cloud")
BROWSER_USE_API_KEY = os.environ.get("BROWSER_USE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

BLACKBOARD_POLL_INTERVAL = 10  # seconds - how often swarm_manager checks for weak agents
AGENT_TASK_TIMEOUT = 300  # seconds - maximum time for a single agent task


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def extract_keywords_from_content(content_description: str) -> str:
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
        print(f"   🔑 Extracted keywords: {keywords}")
        return keywords
    except Exception as e:
        print(f"   ⚠️  Keyword extraction failed: {e}")
        return "trending, viral, popular"  # fallback


async def get_competitor_search_terms(mission_prompt: str) -> List[str]:
    """Generate 3 competitor brand names from mission prompt using OpenAI."""
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
                        "Return ONLY the actual company or product brand names, one per line."
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
        search_terms = []
        for line in search_terms_text.split('\n'):
            cleaned = line.strip().strip('123456789.-)').strip().strip('"').strip(',')
            if cleaned and len(cleaned) > 1:
                search_terms.append(cleaned)
        
        search_terms = search_terms[:3]
        while len(search_terms) < 3:
            search_terms.append(mission_prompt)
        
        print(f"🤖 Generated 3 competitor search terms:")
        for i, term in enumerate(search_terms, 1):
            print(f"   {i}. {term}")
        
        return search_terms
        
    except Exception as e:
        print(f"⚠️  Error calling OpenAI: {e}")
        return [mission_prompt, mission_prompt, mission_prompt]


# ============================================================================
# SWARM ORCHESTRATOR CLASS
# ============================================================================

class SwarmOrchestrator:
    """
    Main orchestrator class implementing Swarm Intelligence with Blackboard Architecture.
    
    Key features:
    - Manages 9 concurrent browser agents
    - Tracks agent energy (risk/reward system)
    - Monitors discoveries (Blackboard)
    - Reassigns weak agents to exploit successful discoveries
    """
    
    def __init__(self):
        self.convex_client = ConvexClient(CONVEX_URL)
        self.browser_client = AsyncBrowserUse(api_key=BROWSER_USE_API_KEY)
        
        # Agent task management
        self.agent_tasks: Dict[int, asyncio.Task] = {}  # agent_id -> Task
        self.agent_sessions: Dict[int, any] = {}  # agent_id -> browser session
        self.agent_search_terms: Dict[int, str] = {}  # agent_id -> current search term
        self.agent_platforms: Dict[int, str] = {}  # agent_id -> platform (tiktok/youtube/duckduckgo)
        
        # Swarm manager control
        self.swarm_manager_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Original mission context
        self.mission_id: Optional[str] = None
        self.original_search_terms: List[str] = []
        
    def get_profile_ids(self) -> List[str]:
        """Return 3 profile IDs for TikTok agents."""
        return [
            "06fb7076-4c7d-4264-b53a-e4726c597ac0",
            "31203964-ed13-454f-a27e-0c3054751a8a",
            "8e063dd1-26ab-40ff-bf10-74813b2933e6"
        ]
    
    # ========================================================================
    # AGENT INITIALIZATION
    # ========================================================================
    
    async def initialize_agents(self, mission):
        """
        Initialize all 9 agents with browser sessions and register them in Convex.
        Each agent starts with 100 energy.
        """
        self.mission_id = mission["_id"]
        prompt = mission["prompt"]
        
        print(f"\n{'='*70}")
        print(f"🚀 INITIALIZING SWARM INTELLIGENCE SYSTEM")
        print(f"{'='*70}\n")
        print(f"Mission: {prompt}\n")
        
        # Generate search terms
        self.original_search_terms = await get_competitor_search_terms(prompt)
        profile_ids = self.get_profile_ids()
        
        live_urls = []
        
        # ====================================================================
        # Agents 1-3: TikTok with profiles
        # ====================================================================
        print(f"📱 Creating TikTok agents (1-3)...")
        for i in range(1, 4):
            search_term = self.original_search_terms[i-1]
            profile_id = profile_ids[i-1]
            
            try:
                session = await self.browser_client.sessions.create(
                    proxy_country_code="us",
                    profile_id=profile_id
                )
                
                self.agent_sessions[i] = session
                self.agent_search_terms[i] = search_term
                self.agent_platforms[i] = "tiktok"
                live_urls.append(session.live_url)
                
                # Register agent in Convex with 100 energy
                self.convex_client.mutation(
                    "agents:updateAgentState",
                    {
                        "agent_id": i,
                        "status": "idle",
                        "current_url": session.live_url,
                        "profile_id": profile_id,
                        "energy": 100  # Starting energy
                    }
                )
                
                print(f"   ✅ Agent {i} (TikTok): {search_term} | Energy: 100")
                
            except Exception as e:
                print(f"   ❌ Agent {i} failed to init: {e}")
                live_urls.append(None)
        
        # ====================================================================
        # Agents 4-6: YouTube Shorts (no profiles)
        # ====================================================================
        print(f"\n🎥 Creating YouTube agents (4-6)...")
        for i in range(4, 7):
            search_term = self.original_search_terms[i-4]
            
            try:
                session = await self.browser_client.sessions.create(
                    proxy_country_code="us"
                )
                
                self.agent_sessions[i] = session
                self.agent_search_terms[i] = search_term
                self.agent_platforms[i] = "youtube"
                live_urls.append(session.live_url)
                
                # Register agent in Convex with 100 energy
                self.convex_client.mutation(
                    "agents:updateAgentState",
                    {
                        "agent_id": i,
                        "status": "idle",
                        "current_url": session.live_url,
                        "profile_id": "none",
                        "energy": 100
                    }
                )
                
                print(f"   ✅ Agent {i} (YouTube): {search_term} | Energy: 100")
                
            except Exception as e:
                print(f"   ❌ Agent {i} failed to init: {e}")
                live_urls.append(None)
        
        # ====================================================================
        # Agents 7-9: DuckDuckGo Web Search (no profiles)
        # ====================================================================
        print(f"\n🦆 Creating DuckDuckGo agents (7-9)...")
        for i in range(7, 10):
            search_term = self.original_search_terms[i-7]
            
            try:
                session = await self.browser_client.sessions.create(
                    proxy_country_code="us"
                )
                
                self.agent_sessions[i] = session
                self.agent_search_terms[i] = search_term
                self.agent_platforms[i] = "duckduckgo"
                live_urls.append(session.live_url)
                
                # Register agent in Convex with 100 energy
                self.convex_client.mutation(
                    "agents:updateAgentState",
                    {
                        "agent_id": i,
                        "status": "idle",
                        "current_url": session.live_url,
                        "profile_id": "none",
                        "energy": 100
                    }
                )
                
                print(f"   ✅ Agent {i} (DuckDuckGo): {search_term} | Energy: 100")
                
            except Exception as e:
                print(f"   ❌ Agent {i} failed to init: {e}")
                live_urls.append(None)
        
        # Update mission with all live URLs
        print(f"\n💾 Updating mission with {len([u for u in live_urls if u])} livestream URLs...")
        update_args = {
            "missionId": str(self.mission_id),
            "liveUrl": live_urls[0] if len(live_urls) > 0 and live_urls[0] else "",
            "sessionId": str(self.agent_sessions[1].id) if 1 in self.agent_sessions else "",
        }
        for idx, url in enumerate(live_urls[1:], start=2):
            if url:
                update_args[f"liveUrl{idx}"] = url
        
        self.convex_client.mutation("missions:updateMissionLivestream", update_args)
        
        print(f"\n✅ All agents initialized!")
        print(f"{'='*70}\n")
    
    # ========================================================================
    # SWARM MANAGER (BLACKBOARD WATCHER)
    # ========================================================================
    
    async def swarm_manager(self):
        """
        **BLACKBOARD ARCHITECTURE - SWARM MANAGER**
        
        This background task polls Convex every 10 seconds to:
        1. Check for weak agents (energy <= 0)
        2. Query the Blackboard (discoveries table) for latest successful find
        3. Reassign weak agents to exploit that discovery
        4. Restart agent tasks with new targeted prompts
        
        This implements the Exploitation strategy in the Exploration/Exploitation
        tradeoff of Swarm Intelligence.
        """
        print(f"\n🧠 SWARM MANAGER STARTED - Monitoring Blackboard every {BLACKBOARD_POLL_INTERVAL}s")
        
        while self.running:
            try:
                await asyncio.sleep(BLACKBOARD_POLL_INTERVAL)
                
                # Query Convex for weak agents
                weak_agents = self.convex_client.query("agents:getWeakAgents")
                
                if not weak_agents or len(weak_agents) == 0:
                    continue  # No weak agents, continue monitoring
                
                print(f"\n{'='*70}")
                print(f"⚠️  SWARM MANAGER: Found {len(weak_agents)} weak agent(s)")
                
                # Query the Blackboard for the latest discovery
                latest_discovery = self.convex_client.query("discoveries:getLatestDiscovery")
                
                if not latest_discovery:
                    print(f"📋 Blackboard is empty - no discoveries to exploit yet")
                    print(f"   Weak agents will continue with original tasks...")
                    continue
                
                # Extract exploitation context from the discovery
                keywords = latest_discovery.get("keywords", "trending content")
                finder_agent_id = latest_discovery.get("found_by_agent_id")
                
                print(f"📋 BLACKBOARD EXPLOITATION:")
                print(f"   Latest discovery by Agent {finder_agent_id}")
                print(f"   Keywords: {keywords}")
                print(f"   Reassigning weak agents to exploit this discovery...\n")
                
                # Reassign each weak agent
                for weak_agent in weak_agents:
                    agent_id = weak_agent["agent_id"]
                    
                    # Skip if this agent doesn't have a session (failed init)
                    if agent_id not in self.agent_sessions:
                        continue
                    
                    platform = self.agent_platforms.get(agent_id, "unknown")
                    
                    print(f"   🔄 Reassigning Agent {agent_id} ({platform}):")
                    print(f"      Old status: {weak_agent['status']}")
                    print(f"      Old energy: {weak_agent['energy']}")
                    
                    # Cancel existing task if running
                    if agent_id in self.agent_tasks and not self.agent_tasks[agent_id].done():
                        self.agent_tasks[agent_id].cancel()
                        try:
                            await self.agent_tasks[agent_id]
                        except asyncio.CancelledError:
                            pass
                        print(f"      ✅ Cancelled old task")
                    
                    # Generate new exploitation prompt
                    new_search_term = f"{keywords}"
                    self.agent_search_terms[agent_id] = new_search_term
                    
                    # Reset energy and update status
                    self.convex_client.mutation(
                        "agents:updateAgentState",
                        {
                            "agent_id": agent_id,
                            "status": "exploiting",
                            "current_url": f"Exploiting: {keywords}",
                            "energy": 100  # Reset energy
                        }
                    )
                    
                    print(f"      🎯 New search: {keywords}")
                    print(f"      ⚡ Energy reset: 100")
                    
                    # Spawn new agent task with exploitation prompt
                    task = asyncio.create_task(
                        self.run_agent_loop(agent_id, new_search_term, exploitation_mode=True)
                    )
                    self.agent_tasks[agent_id] = task
                    
                    print(f"      ✅ Spawned new exploitation task\n")
                
                print(f"{'='*70}\n")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Swarm Manager error: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # ========================================================================
    # AGENT EXECUTION LOOPS
    # ========================================================================
    
    async def run_agent_loop(self, agent_id: int, search_term: str, exploitation_mode: bool = False):
        """
        **AGENT TASK LOOP**
        
        Each agent runs in this loop:
        1. Execute platform-specific analysis task
        2. On success: reset energy to 100, extract keywords, log discovery
        3. On failure: deduct 30 energy
        4. If energy <= 0: mark as weak, let swarm_manager handle reassignment
        5. Repeat
        
        Args:
            agent_id: The agent ID (1-9)
            search_term: What to search for
            exploitation_mode: True if exploiting another agent's discovery
        """
        platform = self.agent_platforms[agent_id]
        
        mode_label = "🎯 EXPLOITING" if exploitation_mode else "🔍 EXPLORING"
        print(f"[Agent {agent_id}] {mode_label} | Platform: {platform} | Search: {search_term}")
        
        while self.running:
            try:
                # Get current energy from Convex
                agents = self.convex_client.query("agents:getAllAgents")
                agent_data = next((a for a in agents if a["agent_id"] == agent_id), None)
                
                if not agent_data:
                    print(f"[Agent {agent_id}] ⚠️  Not found in Convex, stopping...")
                    break
                
                current_energy = agent_data.get("energy", 100)
                
                # Check if agent became weak (should not happen if swarm_manager works)
                if current_energy <= 0:
                    print(f"[Agent {agent_id}] 🔋 Energy depleted ({current_energy}), waiting for reassignment...")
                    # Mark as weak and wait for swarm_manager
                    self.convex_client.mutation(
                        "agents:updateAgentState",
                        {
                            "agent_id": agent_id,
                            "status": "weak",
                            "current_url": "Energy depleted - awaiting reassignment"
                        }
                    )
                    await asyncio.sleep(5)  # Wait for swarm_manager
                    continue
                
                # Update status to searching
                self.convex_client.mutation(
                    "agents:updateAgentState",
                    {
                        "agent_id": agent_id,
                        "status": "exploiting" if exploitation_mode else "searching",
                        "current_url": f"Analyzing: {search_term}",
                        "energy": current_energy
                    }
                )
                
                # ============================================================
                # EXECUTE PLATFORM-SPECIFIC ANALYSIS TASK
                # ============================================================
                success = False
                discoveries_made = 0
                
                try:
                    # Route to platform-specific handler
                    if platform == "tiktok":
                        discoveries_made = await self.analyze_tiktok(agent_id, search_term)
                    elif platform == "youtube":
                        discoveries_made = await self.analyze_youtube(agent_id, search_term)
                    elif platform == "duckduckgo":
                        discoveries_made = await self.analyze_duckduckgo(agent_id, search_term)
                    
                    success = discoveries_made > 0
                    
                except asyncio.TimeoutError:
                    print(f"[Agent {agent_id}] ⏱️  Task timeout")
                    success = False
                except Exception as e:
                    print(f"[Agent {agent_id}] ❌ Task failed: {e}")
                    success = False
                
                # ============================================================
                # RISK/REWARD SYSTEM - UPDATE ENERGY
                # ============================================================
                if success:
                    # SUCCESS: Reset energy to 100
                    new_energy = 100
                    print(f"[Agent {agent_id}] ✅ Success! Energy reset: {current_energy} → {new_energy}")
                    
                    self.convex_client.mutation(
                        "agents:updateAgentEnergy",
                        {
                            "agent_id": agent_id,
                            "energy": new_energy
                        }
                    )
                else:
                    # FAILURE: Deduct 30 energy
                    new_energy = max(0, current_energy - 30)
                    print(f"[Agent {agent_id}] ❌ Failed. Energy deducted: {current_energy} → {new_energy}")
                    
                    self.convex_client.mutation(
                        "agents:updateAgentEnergy",
                        {
                            "agent_id": agent_id,
                            "energy": new_energy
                        }
                    )
                    
                    if new_energy <= 0:
                        print(f"[Agent {agent_id}] ⚠️  Energy depleted! Marked as WEAK")
                        self.convex_client.mutation(
                            "agents:updateAgentState",
                            {
                                "agent_id": agent_id,
                                "status": "weak",
                                "current_url": "Energy depleted"
                            }
                        )
                
                # Small delay before next iteration
                await asyncio.sleep(2)
                
            except asyncio.CancelledError:
                print(f"[Agent {agent_id}] 🛑 Task cancelled")
                break
            except Exception as e:
                print(f"[Agent {agent_id}] ❌ Unexpected error in loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(5)
    
    # ========================================================================
    # PLATFORM-SPECIFIC ANALYSIS METHODS
    # ========================================================================
    
    async def analyze_tiktok(self, agent_id: int, search_term: str) -> int:
        """
        TikTok analysis: Search, click videos, use OCR to detect likes,
        log viral videos (50+ likes) with keywords extracted.
        
        Returns: Number of discoveries made
        """
        session = self.agent_sessions[agent_id]
        discoveries = 0
        
        print(f"[Agent {agent_id}] 🎵 TikTok: Searching for '{search_term}'...")
        
        try:
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
            
            print(f"[Agent {agent_id}] ✅ Search complete, analyzing first video...")
            
            # Phase 2: Click on first viral video
            click_video_task = f"""
            You are on the TikTok search results page for "{search_term}".
            
            Look at all the videos visible on screen.
            Find ONE video that has high engagement (look for high view counts like "100K", "1M", etc.).
            
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
            
            if not current_url:
                print(f"[Agent {agent_id}] ⚠️ Could not find video, no discovery")
                return 0
            
            print(f"[Agent {agent_id}] ✅ Opened video: {current_url[:60]}...")
            
            # Wait for video to load
            await asyncio.sleep(3)
            
            # Phase 3: Take screenshot and use OCR to detect likes
            print(f"[Agent {agent_id}] 📸 Taking screenshot for analysis...")
            screenshot_task = "Take a screenshot of the current TikTok video showing its metrics."
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
                print(f"[Agent {agent_id}] ⚠️ Could not capture screenshot")
                return 0
            
            # Use OpenAI Vision to read likes
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Look at this TikTok video screenshot. Find the heart icon (like button) on the RIGHT side and read the number next to it.

The number might be: "1949", "1.2K", "450K", "1.5M", etc.

Respond with ONLY the number. Examples:
- If you see "1.2K" → respond "1.2K"
- If you see "1949" → respond "1949"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": screenshot_url}
                            }
                        ]
                    }
                ],
                max_tokens=50
            )
            
            ocr_result = response.choices[0].message.content.strip()
            print(f"[Agent {agent_id}] 📊 Likes: {ocr_result}")
            
            # Parse likes count
            likes_count = 0
            if 'M' in ocr_result.upper():
                likes_count = int(float(re.sub(r'[^0-9.]', '', ocr_result)) * 1_000_000)
            elif 'K' in ocr_result.upper():
                likes_count = int(float(re.sub(r'[^0-9.]', '', ocr_result)) * 1_000)
            else:
                likes_count = int(re.sub(r'[^0-9]', '', ocr_result) or '0')
            
            # Check if viral (50+ likes threshold)
            if likes_count >= 50:
                discoveries = 1
                keywords = await extract_keywords_from_content(f"TikTok video about {search_term}")
                
                self.convex_client.mutation(
                    "discoveries:logDiscovery",
                    {
                        "video_url": current_url,
                        "thumbnail": screenshot_url or "https://placeholder.com/150",
                        "found_by_agent_id": agent_id,
                        "keywords": keywords
                    }
                )
                
                print(f"[Agent {agent_id}] ✨ VIRAL! {likes_count} likes | Keywords: {keywords}")
            else:
                print(f"[Agent {agent_id}] ❌ Not viral ({likes_count} likes < 50)")
            
        except Exception as e:
            print(f"[Agent {agent_id}] ❌ Error: {e}")
        
        return discoveries
    
    async def analyze_youtube(self, agent_id: int, search_term: str) -> int:
        """
        YouTube Shorts analysis: Search, navigate shorts, use OCR to detect likes,
        log viral shorts (50+ likes) with keywords.
        
        Returns: Number of discoveries made
        """
        session = self.agent_sessions[agent_id]
        discoveries = 0
        
        print(f"[Agent {agent_id}] 🎥 YouTube: Searching for '{search_term}'...")
        
        try:
            # Phase 1: Search for content
            search_task = f"""
            Go to YouTube (youtube.com).
            
            Use the search bar to search for: "{search_term}"
            
            Wait for search results to load. Look for Shorts videos.
            """
            
            async for step in self.browser_client.run(
                search_task,
                session_id=session.id,
                start_url="https://www.youtube.com",
                max_steps=20,
                vision=True,
            ):
                pass  # Complete search
            
            print(f"[Agent {agent_id}] ✅ Search complete, finding first Short...")
            
            # Phase 2: Click on first Short
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
            
            # Wait for Short to load
            await asyncio.sleep(3)
            
            # Get current URL
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
            
            if not current_url or "youtube.com" not in current_url:
                print(f"[Agent {agent_id}] ⚠️ Could not find Short, no discovery")
                return 0
            
            print(f"[Agent {agent_id}] ✅ Opened Short: {current_url[:60]}...")
            
            # Phase 3: Take screenshot and use OCR to detect likes
            print(f"[Agent {agent_id}] 📸 Taking screenshot for analysis...")
            screenshot_task = "Take a screenshot of the current YouTube Short."
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
                print(f"[Agent {agent_id}] ⚠️ Could not capture screenshot")
                return 0
            
            # Use OpenAI Vision to read likes
            from openai import AsyncOpenAI
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

The number might be: "1.5K", "234", "12K", "1.5M", etc.

Respond with ONLY the number. Examples:
- If you see "1.5K" → respond "1.5K"
- If you see "234" → respond "234"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": screenshot_url}
                            }
                        ]
                    }
                ],
                max_tokens=50
            )
            
            ocr_result = response.choices[0].message.content.strip()
            print(f"[Agent {agent_id}] 📊 Likes: {ocr_result}")
            
            # Parse likes count
            likes_count = 0
            if 'M' in ocr_result.upper():
                likes_count = int(float(re.sub(r'[^0-9.]', '', ocr_result)) * 1_000_000)
            elif 'K' in ocr_result.upper():
                likes_count = int(float(re.sub(r'[^0-9.]', '', ocr_result)) * 1_000)
            else:
                likes_count = int(re.sub(r'[^0-9]', '', ocr_result) or '0')
            
            # Check if viral (50+ likes threshold)
            if likes_count >= 50:
                discoveries = 1
                keywords = await extract_keywords_from_content(f"YouTube short about {search_term}")
                
                self.convex_client.mutation(
                    "discoveries:logDiscovery",
                    {
                        "video_url": current_url,
                        "thumbnail": screenshot_url or "https://placeholder.com/150",
                        "found_by_agent_id": agent_id,
                        "keywords": keywords
                    }
                )
                
                print(f"[Agent {agent_id}] ✨ VIRAL! {likes_count} likes | Keywords: {keywords}")
            else:
                print(f"[Agent {agent_id}] ❌ Not viral ({likes_count} likes < 50)")
            
        except Exception as e:
            print(f"[Agent {agent_id}] ❌ Error: {e}")
        
        return discoveries
    
    async def analyze_duckduckgo(self, agent_id: int, search_term: str) -> int:
        """
        DuckDuckGo web search: Search, visit top results, extract info with LLM,
        log relevant pages with keywords.
        
        Returns: Number of discoveries made
        """
        session = self.agent_sessions[agent_id]
        discoveries = 0
        
        print(f"[Agent {agent_id}] 🦆 DuckDuckGo: Searching for '{search_term}'...")
        
        try:
            # Phase 1: Search on DuckDuckGo
            search_task = f"""
            Go to DuckDuckGo (duckduckgo.com).
            
            Use the search box to search for: "{search_term}"
            
            Wait for search results to load.
            """
            
            async for step in self.browser_client.run(
                search_task,
                session_id=session.id,
                start_url="https://www.duckduckgo.com",
                max_steps=15,
                vision=True,
            ):
                pass  # Complete search
            
            print(f"[Agent {agent_id}] ✅ Search complete, visiting first result...")
            
            # Phase 2: Click on first search result
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
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Get current URL
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
                print(f"[Agent {agent_id}] ⚠️ Still on search page, no discovery")
                return 0
            
            print(f"[Agent {agent_id}] ✅ Visiting: {current_url[:60]}...")
            
            # Phase 3: Take screenshot and extract information
            print(f"[Agent {agent_id}] 📸 Taking screenshot for analysis...")
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
                print(f"[Agent {agent_id}] ⚠️ Could not capture screenshot")
                return 0
            
            # Use OpenAI Vision to extract information
            from openai import AsyncOpenAI
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

Extract key information:
1. What is the main product/service?
2. Key features or benefits?
3. Any pricing info?
4. Social proof (testimonials, ratings)?

Respond in 2-3 sentences. If the page is RELEVANT to "{search_term}", start with "RELEVANT:". If not relevant or just a generic list/directory, start with "NOT RELEVANT:"."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": screenshot_url}
                            }
                        ]
                    }
                ],
                max_tokens=200
            )
            
            extraction_result = response.choices[0].message.content.strip()
            print(f"[Agent {agent_id}] 📊 {extraction_result[:100]}...")
            
            # Check if relevant
            if extraction_result.upper().startswith("RELEVANT:"):
                discoveries = 1
                keywords = await extract_keywords_from_content(extraction_result)
                
                self.convex_client.mutation(
                    "discoveries:logDiscovery",
                    {
                        "video_url": current_url,
                        "thumbnail": screenshot_url or "https://placeholder.com/150",
                        "found_by_agent_id": agent_id,
                        "keywords": keywords
                    }
                )
                
                print(f"[Agent {agent_id}] ✨ RELEVANT! Keywords: {keywords}")
            else:
                print(f"[Agent {agent_id}] ❌ Not relevant to search term")
            
        except Exception as e:
            print(f"[Agent {agent_id}] ❌ Error: {e}")
        
        return discoveries
    
    # ========================================================================
    # MAIN ORCHESTRATION
    # ========================================================================
    
    async def start_swarm(self, mission):
        """
        **MAIN ENTRY POINT**
        
        1. Initialize all 9 agents with browser sessions
        2. Start swarm_manager (Blackboard watcher)
        3. Launch all 9 agent tasks concurrently
        4. Monitor and manage the swarm
        """
        try:
            self.running = True
            
            # Initialize agents and create browser sessions
            await self.initialize_agents(mission)
            
            # Start the Swarm Manager (Blackboard watcher)
            self.swarm_manager_task = asyncio.create_task(self.swarm_manager())
            
            print(f"\n{'='*70}")
            print(f"🐝 LAUNCHING SWARM - 9 agents working concurrently")
            print(f"{'='*70}\n")
            
            # Launch all agent tasks
            for agent_id in self.agent_sessions.keys():
                search_term = self.agent_search_terms[agent_id]
                task = asyncio.create_task(
                    self.run_agent_loop(agent_id, search_term, exploitation_mode=False)
                )
                self.agent_tasks[agent_id] = task
            
            # Wait for all tasks (they run indefinitely until cancelled)
            await asyncio.gather(*self.agent_tasks.values(), return_exceptions=True)
            
        except KeyboardInterrupt:
            print(f"\n\n{'='*70}")
            print(f"⏹️  SHUTTING DOWN SWARM")
            print(f"{'='*70}\n")
            await self.cleanup()
        except Exception as e:
            print(f"\n❌ Swarm error: {e}")
            import traceback
            traceback.print_exc()
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up all agent tasks and browser sessions."""
        self.running = False
        
        # Cancel swarm manager
        if self.swarm_manager_task and not self.swarm_manager_task.done():
            self.swarm_manager_task.cancel()
            try:
                await self.swarm_manager_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all agent tasks
        for agent_id, task in self.agent_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close all browser sessions
        for agent_id, session in self.agent_sessions.items():
            try:
                await self.browser_client.sessions.stop(session.id)
                await self.browser_client.sessions.delete(session.id)
                print(f"   ✅ Agent {agent_id} session cleaned up")
            except Exception as e:
                print(f"   ⚠️  Agent {agent_id} cleanup error: {e}")
        
        print(f"\n✅ Swarm shutdown complete\n")


# ============================================================================
# MISSION WATCHER (Polls for new missions from Convex)
# ============================================================================

async def watch_missions():
    """
    Continuously poll Convex for new missions.
    When a new mission is detected, launch the swarm.
    """
    convex_client = ConvexClient(CONVEX_URL)
    last_mission_id = None
    
    print(f"\n{'='*70}")
    print(f"🔍 MISSION WATCHER STARTED")
    print(f"📡 Connected to Convex: {CONVEX_URL}")
    print(f"{'='*70}\n")
    
    while True:
        try:
            mission = convex_client.query("missions:getLatestMission")
            
            if mission and mission["_id"] != last_mission_id:
                print(f"\n\n{'='*70}")
                print(f"🆕 NEW MISSION DETECTED!")
                print(f"{'='*70}")
                print(f"Mission ID: {mission['_id']}")
                print(f"Prompt: {mission['prompt']}\n")
                
                # Launch the swarm for this mission
                orchestrator = SwarmOrchestrator()
                await orchestrator.start_swarm(mission)
                
                last_mission_id = mission["_id"]
            
            await asyncio.sleep(3)  # Poll every 3 seconds
            
        except KeyboardInterrupt:
            print("\n⏹️  Mission watcher stopped")
            break
        except Exception as e:
            print(f"❌ Mission watcher error: {e}")
            await asyncio.sleep(3)


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Entry point."""
    # Check environment variables
    if not BROWSER_USE_API_KEY:
        print("❌ Error: BROWSER_USE_API_KEY environment variable not set")
        print("   Get your API key from: https://cloud.browser-use.com/settings?tab=api-keys")
        sys.exit(1)
    
    if not OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Get your API key from: https://platform.openai.com/api-keys")
        sys.exit(1)
    
    # Start mission watcher
    await watch_missions()


if __name__ == "__main__":
    asyncio.run(main())
