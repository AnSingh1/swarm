# SwarmCast Orchestrator - Phase 2

The Python backend that manages 10 concurrent AI browser agents using Browser Use SDK.

## Quick Start (Hackathon Mode)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Make sure your `.env` file has:
```bash
BROWSER_USE_API_KEY=your_key_here
```

### 3. Test with Limited Agents (RECOMMENDED FIRST)

**The orchestrator is already configured to run with just 2 agents for testing!**

Line 107 in `orchestrator.py` is set to:
```python
# For testing, start with just 2 agents (COMMENT OUT to use all 10 agents)
AGENT_CONFIG = [AGENT_CONFIG[0], AGENT_CONFIG[3]]  # Only Instagram (tim) and YouTube
```

Run the orchestrator:
```bash
export BROWSER_USE_API_KEY=bu_ydoAyk34xD4xLVAdvgAC-SGA0Egwh6sXTQ5TRRWn-DM
python orchestrator.py
```

### 4. Verify in Your Debug UI

1. Keep your Next.js dev server running (`npm run dev`)
2. Open http://localhost:3000 in your browser
3. Create a mission in the UI (e.g., "Find trending AI videos")
4. Watch the orchestrator terminal for agent activity
5. Verify that agent states update in your debug UI in real-time:
   - Status changes from "idle" → "searching" → "found_trend"
   - Discoveries appear in the right column

### 5. Unleash the Full Swarm

Once you've verified it works with 2 agents:
1. Comment out the test line in `orchestrator.py`
2. Restart the orchestrator
3. All 10 agents will run concurrently

## Architecture

### Agent Configuration

- **Agents 1-3**: Instagram Reels (using Browser Use profiles: `tim`, `sing`, `vinny`)
- **Agents 4-5**: YouTube Shorts
- **Agents 6-7**: TikTok
- **Agents 8-10**: Google Search for trending content

### How It Works

1. **Polling Loop**: Checks Convex every 5 seconds for missions with `status: "active"`
2. **Swarm Launch**: When a mission is found, launches all agents concurrently
3. **Agent Execution**: Each agent:
   - Updates its status to "searching" in Convex
   - Constructs a platform-specific prompt
   - Uses Browser Use SDK to automate browser actions
   - Extracts video URL and thumbnail
   - Logs discovery to Convex
   - Updates status to "found_trend" (or "weak" on failure)
4. **Concurrency Control**: Uses `asyncio.Semaphore(10)` to limit concurrent execution
5. **Error Handling**: Individual agent failures don't crash the entire swarm

## Debugging Tips

### Enable Browser Visibility

In `orchestrator.py`, line 210:
```python
headless=False,  # Set to False to see browser windows
```

### Reduce Timeout

If agents are taking too long, adjust line 226:
```python
timeout=60.0  # Reduce from 120 to 60 seconds
```

### Check Convex Logs

Visit your Convex dashboard:
https://dashboard.convex.dev/d/flexible-retriever-257

### Common Issues

**"BROWSER_USE_API_KEY not set"**
- Make sure `.env` file is in the project root
- Run `export BROWSER_USE_API_KEY=your_key` in terminal

**"No active missions"**
- Create a mission in your Next.js UI
- Check that mission status is "active" in Convex

**Agents stuck in "searching" status**
- Check orchestrator terminal for error messages
- Verify Browser Use API key is valid
- Try reducing the number of concurrent agents

## Production Considerations

For a real deployment, you'd want to:
- Add proper logging (use `logging` module instead of `print`)
- Implement Laminar AI for eval tracking
- Add retry logic for transient failures
- Store agent performance metrics
- Implement agent reassignment when status is "weak"
- Add health checks and monitoring
- Use a process manager (PM2, systemd, etc.)

## Browser Use Cloud Profiles

The Instagram agents (1-3) use specific Browser Use cloud profiles:
- `tim`: Agent 1
- `sing`: Agent 2
- `vinny`: Agent 3

These profiles should be pre-configured in your Browser Use dashboard with logged-in Instagram sessions.

## Stopping the Orchestrator

Press `Ctrl+C` to gracefully shutdown the orchestrator.
