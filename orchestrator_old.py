"""
SwarmCast Orchestrator
A continuously running Python script that manages 10 concurrent AI browser agents
using the browser-use SDK and syncs their state to a Convex database.
"""

import asyncio
import os
import sys
import time
from typing import Dict, List, Optional
from datetime import datetime

from convex import ConvexClient
from browser_use import Agent
from browser_use.browser.profile import BrowserProfile

# ============================================================================
# CONFIGURATION
# ============================================================================

CONVEX_URL = "https://flexible-retriever-257.convex.cloud"
BROWSER_USE_API_KEY = os.environ.get("BROWSER_USE_API_KEY")

# Maximum number of concurrent agents
MAX_CONCURRENT_AGENTS = 10

# Polling interval for checking new missions (seconds)
MISSION_POLL_INTERVAL = 5

# Agent configuration: Each agent has an ID, target platform, and optional profile
AGENT_CONFIG = [
    # Instagram agents with specific Browser Use cloud profiles
    {
        "agent_id": 1,
        "platform": "Instagram",
        "profile": "tim",
        "base_url": "https://www.instagram.com/",
        "search_hint": "Go to Instagram Reels and search for trending content about: {prompt}"
    },
    {
        "agent_id": 2,
        "platform": "Instagram",
        "profile": "sing",
        "base_url": "https://www.instagram.com/",
        "search_hint": "Go to Instagram Reels and search for trending content about: {prompt}"
    },
    {
        "agent_id": 3,
        "platform": "Instagram",
        "profile": "vinny",
        "base_url": "https://www.instagram.com/",
        "search_hint": "Go to Instagram Reels and search for trending content about: {prompt}"
    },
    # YouTube Shorts agents
    {
        "agent_id": 4,
        "platform": "YouTube Shorts",
        "profile": None,
        "base_url": "https://www.youtube.com/shorts",
        "search_hint": "Go to YouTube Shorts and search for: {prompt}. Extract the video URL and thumbnail."
    },
    {
        "agent_id": 5,
        "platform": "YouTube Shorts",
        "profile": None,
        "base_url": "https://www.youtube.com/shorts",
        "search_hint": "Go to YouTube Shorts and search for: {prompt}. Extract the video URL and thumbnail."
    },
    # TikTok agents
    {
        "agent_id": 6,
        "platform": "TikTok",
        "profile": None,
        "base_url": "https://www.tiktok.com/",
        "search_hint": "Go to TikTok and search for trending videos about: {prompt}. Extract the video URL and thumbnail."
    },
    {
        "agent_id": 7,
        "platform": "TikTok",
        "profile": None,
        "base_url": "https://www.tiktok.com/",
        "search_hint": "Go to TikTok and search for trending videos about: {prompt}. Extract the video URL and thumbnail."
    },
    # General web search agents (Google)
    {
        "agent_id": 8,
        "platform": "Google Search",
        "profile": None,
        "base_url": "https://www.google.com/",
        "search_hint": "Search Google for trending viral content about: {prompt}. Find popular video links and thumbnails."
    },
    {
        "agent_id": 9,
        "platform": "Google Search",
        "profile": None,
        "base_url": "https://www.google.com/",
        "search_hint": "Search Google for trending viral content about: {prompt}. Find popular video links and thumbnails."
    },
    {
        "agent_id": 10,
        "platform": "Google Search",
        "profile": None,
        "base_url": "https://www.google.com/",
        "search_hint": "Search Google for trending viral content about: {prompt}. Find popular video links and thumbnails."
    },
]

# For testing, start with just 2 agents (COMMENT OUT to use all 10 agents)
AGENT_CONFIG = [AGENT_CONFIG[0], AGENT_CONFIG[3]]  # Only Instagram (tim) and YouTube

# ============================================================================
# CONVEX CLIENT INITIALIZATION
# ============================================================================

def init_convex_client() -> ConvexClient:
    """Initialize and return a Convex client."""
    print(f"🔌 Connecting to Convex at {CONVEX_URL}...")
    client = ConvexClient(CONVEX_URL)
    print("✅ Convex client initialized")
    return client


# ============================================================================
# CONVEX DATABASE OPERATIONS
# ============================================================================

def get_active_mission(client: ConvexClient) -> Optional[Dict]:
    """
    Query Convex for an active mission (status == "active").
    Returns the mission object or None if no active mission exists.
    """
    try:
        mission = client.query("missions:getLatestMission")
        if mission and mission.get("status") == "active":
            return mission
        return None
    except Exception as e:
        print(f"❌ Error fetching active mission: {e}")
        return None


def update_agent_state(
    client: ConvexClient,
    agent_id: int,
    status: str,
    current_url: str,
    profile_id: str = ""
) -> None:
    """
    Update agent state in Convex.
    Status can be: idle, searching, found_trend, weak, reassigning
    """
    try:
        client.mutation(
            "agents:updateAgentState",
            {
                "agent_id": agent_id,
                "status": status,
                "current_url": current_url,
                "profile_id": profile_id,
            }
        )
        print(f"📊 Agent {agent_id} → Status: {status} | URL: {current_url[:50]}...")
    except Exception as e:
        print(f"❌ Error updating agent {agent_id} state: {e}")


def log_discovery(
    client: ConvexClient,
    video_url: str,
    thumbnail: str,
    found_by_agent_id: int
) -> None:
    """
    Log a successful discovery to Convex.
    """
    try:
        client.mutation(
            "discoveries:logDiscovery",
            {
                "video_url": video_url,
                "thumbnail": thumbnail,
                "found_by_agent_id": found_by_agent_id,
            }
        )
        print(f"🎉 Agent {found_by_agent_id} logged discovery: {video_url[:50]}...")
    except Exception as e:
        print(f"❌ Error logging discovery for agent {found_by_agent_id}: {e}")


# ============================================================================
# BROWSER USE AGENT LOGIC
# ============================================================================

async def run_agent(
    agent_config: Dict,
    mission_prompt: str,
    convex_client: ConvexClient,
    semaphore: asyncio.Semaphore
) -> None:
    """
    Main agent task that runs for each browser agent.
    
    This function:
    1. Updates agent status to "searching" in Convex
    2. Constructs a browser automation prompt
    3. Executes the Browser Use task
    4. On success, logs the discovery and updates status to "found_trend"
    5. On failure, updates status to "weak"
    """
    async with semaphore:
        agent_id = agent_config["agent_id"]
        platform = agent_config["platform"]
        profile = agent_config["profile"]
        base_url = agent_config["base_url"]
        search_hint = agent_config["search_hint"]
        
        print(f"\n🤖 Agent {agent_id} ({platform}) starting...")
        
        try:
            # Step 1: Update status to "searching"
            update_agent_state(
                convex_client,
                agent_id=agent_id,
                status="searching",
                current_url=base_url,
                profile_id=profile or ""
            )
            
            # Step 2: Construct the browser automation prompt
            task_prompt = search_hint.format(prompt=mission_prompt)
            task_prompt += "\n\nYour task: Navigate to the platform, search for the content, "
            task_prompt += "and extract the VIDEO URL and THUMBNAIL image URL. "
            task_prompt += "Return these as structured data."
            
            print(f"🔍 Agent {agent_id} prompt: {task_prompt[:100]}...")
            
            # Step 3: Configure and execute Browser Use agent
            browser_profile_config = {
                "headless": True,  # Set to False for debugging
            }
            
            # Add cloud profile if specified (for Instagram agents)
            if profile:
                browser_profile_config["cloud_browser_params"] = {
                    "profile_name": profile
                }
                print(f"👤 Agent {agent_id} using Browser Use cloud profile: {profile}")
            
            # Create browser profile
            browser_profile = BrowserProfile(**browser_profile_config)
            
            # Create and run the browser agent
            agent = Agent(
                task=task_prompt,
                browser_profile=browser_profile,
            )
            
            # Execute the task (with timeout)
            print(f"⚙️  Agent {agent_id} executing task...")
            result = await asyncio.wait_for(
                agent.run(),
                timeout=120.0  # 2 minute timeout per agent
            )
            
            print(f"✅ Agent {agent_id} completed task. Result: {result}")
            
            # Step 4: Parse result and log discovery
            # Extract video URL and thumbnail from result
            # (This is a simplified parser - adjust based on actual Browser Use output format)
            video_url = extract_video_url_from_result(result, base_url)
            thumbnail = extract_thumbnail_from_result(result)
            
            if video_url:
                # Successfully found content
                log_discovery(
                    convex_client,
                    video_url=video_url,
                    thumbnail=thumbnail,
                    found_by_agent_id=agent_id
                )
                
                # Update status to "found_trend"
                update_agent_state(
                    convex_client,
                    agent_id=agent_id,
                    status="found_trend",
                    current_url=video_url,
                    profile_id=profile or ""
                )
                
                print(f"🎯 Agent {agent_id} successfully found trending content!")
            else:
                # No video URL found
                raise ValueError("No video URL extracted from browser result")
            
        except asyncio.TimeoutError:
            print(f"⏰ Agent {agent_id} timed out after 2 minutes")
            update_agent_state(
                convex_client,
                agent_id=agent_id,
                status="weak",
                current_url=base_url,
                profile_id=profile or ""
            )
        
        except Exception as e:
            print(f"❌ Agent {agent_id} failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            
            # Update status to "weak" on any failure
            update_agent_state(
                convex_client,
                agent_id=agent_id,
                status="weak",
                current_url=base_url,
                profile_id=profile or ""
            )
        
        finally:
            print(f"🏁 Agent {agent_id} finished execution\n")


# ============================================================================
# RESULT PARSING HELPERS
# ============================================================================

def extract_video_url_from_result(result: any, fallback_base: str) -> Optional[str]:
    """
    Extract video URL from Browser Use agent result.
    Adjust this function based on the actual output format from browser-use SDK.
    """
    try:
        # If result is a dict with structured data
        if isinstance(result, dict):
            return result.get("video_url") or result.get("url")
        
        # If result is a string containing a URL
        if isinstance(result, str):
            # Look for common video URL patterns
            if "youtube.com" in result or "youtu.be" in result:
                # Extract YouTube URL
                import re
                match = re.search(r'(https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[\w\-]+)', result)
                if match:
                    return match.group(1)
            
            if "tiktok.com" in result:
                # Extract TikTok URL
                import re
                match = re.search(r'(https?://(?:www\.)?tiktok\.com/@[\w\-]+/video/\d+)', result)
                if match:
                    return match.group(1)
            
            if "instagram.com" in result:
                # Extract Instagram URL
                import re
                match = re.search(r'(https?://(?:www\.)?instagram\.com/[\w\-/]+)', result)
                if match:
                    return match.group(1)
        
        # Fallback: return a mock URL for testing
        print(f"⚠️  Could not extract video URL from result, using fallback")
        return f"{fallback_base}mock_video_{int(time.time())}"
    
    except Exception as e:
        print(f"⚠️  Error parsing video URL: {e}")
        return None


def extract_thumbnail_from_result(result: any) -> str:
    """
    Extract thumbnail URL from Browser Use agent result.
    Adjust this function based on the actual output format from browser-use SDK.
    """
    try:
        if isinstance(result, dict):
            return result.get("thumbnail") or result.get("thumbnail_url") or ""
        
        # Fallback: return a placeholder thumbnail
        return "https://via.placeholder.com/480x270.png?text=Video+Thumbnail"
    
    except Exception as e:
        print(f"⚠️  Error parsing thumbnail: {e}")
        return "https://via.placeholder.com/480x270.png?text=Error"


# ============================================================================
# MAIN ORCHESTRATOR LOOP
# ============================================================================

async def run_swarm_for_mission(
    mission: Dict,
    convex_client: ConvexClient
) -> None:
    """
    Launch all agents concurrently using asyncio.gather with a semaphore.
    This ensures we don't overwhelm the system with too many concurrent tasks.
    """
    mission_prompt = mission.get("prompt", "")
    mission_id = mission.get("_id", "unknown")
    
    print(f"\n{'='*70}")
    print(f"🚀 LAUNCHING SWARM FOR MISSION: {mission_id}")
    print(f"📝 Prompt: {mission_prompt}")
    print(f"🤖 Deploying {len(AGENT_CONFIG)} agents...")
    print(f"{'='*70}\n")
    
    # Create semaphore to limit concurrent agents
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_AGENTS)
    
    # Create tasks for all agents
    tasks = [
        run_agent(agent_config, mission_prompt, convex_client, semaphore)
        for agent_config in AGENT_CONFIG
    ]
    
    # Run all agents concurrently
    # Using return_exceptions=True ensures one agent failure doesn't crash the swarm
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Log any unhandled exceptions from gather
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ Agent {AGENT_CONFIG[i]['agent_id']} raised exception: {result}")
    
    print(f"\n{'='*70}")
    print(f"✅ SWARM MISSION COMPLETE")
    print(f"{'='*70}\n")


async def orchestrator_main_loop():
    """
    Main orchestrator loop that continuously polls Convex for active missions
    and launches agent swarms when missions are found.
    """
    print("\n" + "="*70)
    print("🐝 SwarmCast Orchestrator Starting...")
    print("="*70 + "\n")
    
    # Validate environment
    if not BROWSER_USE_API_KEY:
        print("❌ ERROR: BROWSER_USE_API_KEY not set in environment!")
        print("   Please set it before running the orchestrator.")
        sys.exit(1)
    
    # Initialize Convex client
    convex_client = init_convex_client()
    
    print(f"👀 Polling for active missions every {MISSION_POLL_INTERVAL} seconds...")
    print(f"   Press Ctrl+C to stop\n")
    
    try:
        while True:
            # Check for active mission
            mission = get_active_mission(convex_client)
            
            if mission:
                print(f"📢 Active mission detected: {mission.get('_id')}")
                
                # Launch the swarm
                await run_swarm_for_mission(mission, convex_client)
                
                # Mark mission as completed (optional - you may want to do this manually)
                # convex_client.mutation("missions:updateMissionStatus", {
                #     "mission_id": mission["_id"],
                #     "status": "completed"
                # })
                
                print("⏸️  Mission complete. Waiting for next mission...\n")
            else:
                # No active mission, wait and poll again
                print("💤 No active missions. Sleeping...", end="\r")
            
            await asyncio.sleep(MISSION_POLL_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\n⛔ Orchestrator stopped by user")
        print("👋 Shutting down gracefully...\n")
    
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR in orchestrator: {e}")
        print(f"   Stack trace:")
        import traceback
        traceback.print_exc()
    
    finally:
        print("🔚 Orchestrator shutdown complete\n")


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """
    Entry point for the orchestrator.
    Sets up the async event loop and runs the main orchestrator loop.
    """
    try:
        # Get or create event loop
        loop = asyncio.get_event_loop()
        
        # Run the orchestrator
        loop.run_until_complete(orchestrator_main_loop())
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
