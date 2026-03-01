# Mission Livestream Integration

## Overview
When you create a new mission in the SwarmCast UI, the system automatically:
1. Starts a live browser session using the 'pro' profile (already logged into TikTok)
2. Goes to TikTok search and searches for your mission prompt
3. Scrolls through and analyzes videos for relevance
4. Logs matching videos to the discoveries database
5. Displays the live browser view in an iframe on the frontend

## Prerequisites

### 1. Create a Browser Use Profile
You need a profile named 'pro' that's already logged into TikTok:

```bash
# Option 1: Sync your local browser cookies to the cloud
export BROWSER_USE_API_KEY='your_key'
curl -fsSL https://browser-use.com/profile.sh | sh
# Then name it 'pro' when prompted

# Option 2: Use the Browser Use dashboard to create a profile
# Go to https://cloud.browser-use.com/profiles
# Create a profile named 'pro' and login to TikTok manually
```

## Setup

### 1. Install Dependencies
```bash
pip install browser-use-sdk convex openai
```

### 2. Set Environment Variables
```bash
export BROWSER_USE_API_KEY='your_browser_use_key'
export OPENAI_API_KEY='your_openai_key'
export CONVEX_URL='https://flexible-retriever-257.convex.cloud'
```

Get your Browser Use API key from: https://cloud.browser-use.com/settings?tab=api-keys
Get your OpenAI API key from: https://platform.openai.com/api-keys

### 3. Push Convex Schema
```bash
npx convex dev
```

This will update the database schema with the new livestream fields.

## Running the System

### Start the Mission Watcher
In one terminal:
```bash
./start_mission_watcher.sh
# or
python mission_livestream_watcher.py
```

This script watches for new missions and automatically starts TikTok livestreams.

### Start the Frontend
In another terminal:
```bash
npm run dev
```

### Start the Orchestrator (Optional)
If you want to run the full agent swarm:
```bash
./start_orchestrator.sh
```

## How It Works

1. **AI Competitor Detection**: When you create a mission like "Find AI meeting note taker videos", GPT-4o analyzes it and returns the top competitor (e.g., "Granola")

2. **TikTok Search**: The agent searches TikTok for that competitor brand

3. **Methodical Analysis**: For each video (up to 20):
   - Click on the video
   - Wait for it to load (3 seconds)
   - Read the metrics (views, likes, comments)
   - Determine if it's viral (>100K views OR >10K likes)
   - Log it as a discovery if viral
   - Go back to search results
   - Repeat

4. **Live Streaming**: Watch everything happen in real-time via the iframe in your frontend

5. **Discovery Database**: All viral videos are automatically saved to your Convex database

## Usage

1. Make sure your 'pro' profile exists and is logged into TikTok
2. Set your `OPENAI_API_KEY` environment variable
3. Open the frontend at http://localhost:3000
4. Enter a mission prompt (e.g., "AI meeting note taker", "productivity app")
5. Click "Create Mission"
6. Watch as:
   - GPT-4o identifies the competitor (e.g., "Granola")
   - The agent searches TikTok for that competitor
   - Each video is analyzed one by one
   - Viral videos appear in "Latest Discoveries"

## Architecture

```
User creates mission → Convex database
                            ↓
            Mission Watcher detects new mission
                            ↓
            Browser Use Cloud creates session with 'pro' profile
                            ↓
            TikTok search starts (already logged in via profile)
                            ↓
            Agent scrolls, analyzes, and extracts relevant videos
                            ↓
    Discoveries logged to Convex → Frontend displays in "Latest Discoveries"
                            ↓
    Live URL stored in mission record → Frontend displays iframe
```

## Files

- `mission_livestream_watcher.py` - Watches for new missions and starts livestreams
- `start_mission_watcher.sh` - Convenience script to start the watcher
- `livestream_tiktok.py` - Standalone script for testing TikTok livestreaming
- `convex/schema.ts` - Updated with `liveUrl`, `sessionId`, `shareUrl` fields
- `convex/missions.ts` - Added `updateMissionLivestream` mutation
- `app/page.tsx` - Updated to display livestream iframe

## Features

- **AI-Powered Competitor Search**: Uses GPT-4o to automatically identify competitor brands from your mission prompt
- **No Login Required**: Uses Browser Use profiles - TikTok session persists across runs
- **Methodical Video Analysis**: Analyzes each video one at a time with proper timing
- **Metrics-Based Filtering**: Only logs videos with >100K views or >10K likes
- **Real-time Viewing**: Watch the browser navigate TikTok live
- **Automatic Discovery Logging**: Viral videos are logged to your database
- **Automatic Session Management**: Sessions are created and cleaned up automatically
- **Share Links**: Optionally creates shareable public links
- **Vision Mode**: Uses screenshot capability for better video analysis

## Troubleshooting

### Profile 'pro' not found
- Make sure you've created a profile named 'pro' in Browser Use
- Use the profile sync script: `curl -fsSL https://browser-use.com/profile.sh | sh`
- Or create it manually at https://cloud.browser-use.com/profiles

### Not logged into TikTok
- The 'pro' profile needs to be logged into TikTok first
- Create a session manually, login to TikTok, then save the profile
- Profile state persists across sessions (cookies, localStorage)

### No livestream appearing
- Check that `mission_livestream_watcher.py` is running
- Verify your `BROWSER_USE_API_KEY` is set correctly
- Check the console for error messages

### Iframe not loading
- Some browsers block iframes - try a different browser
- Check browser console for security errors
- Verify the `liveUrl` is present in the mission record

### No discoveries being logged
- Check the terminal output for "✨ Logged discovery" messages
- The agent needs to find TikTok URLs in the page
- Try a more specific mission prompt for better matching
