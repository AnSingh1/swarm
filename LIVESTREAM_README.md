# Mission Livestream Integration

## Overview
When you create a new mission in the SwarmCast UI, the system automatically:
1. Starts a live browser session
2. Goes to TikTok and opens the "For You" feed
3. Scrolls through videos
4. Displays the live browser view in an iframe on the frontend

## Setup

### 1. Install Dependencies
```bash
pip install browser-use-sdk convex
```

### 2. Set Environment Variables
```bash
export BROWSER_USE_API_KEY='your_key_here'
export CONVEX_URL='https://flexible-retriever-257.convex.cloud'
```

Get your Browser Use API key from: https://cloud.browser-use.com/settings?tab=api-keys

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

## Usage

1. Open the frontend at http://localhost:3000
2. Enter a mission prompt (e.g., "Find trending dance videos")
3. Click "Create Mission"
4. Watch as the livestream automatically appears showing the browser navigating TikTok in real-time!

## Architecture

```
User creates mission → Convex database
                            ↓
            Mission Watcher detects new mission
                            ↓
            Browser Use Cloud creates session
                            ↓
            TikTok automation starts (scroll, browse)
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

- **Real-time Viewing**: Watch the browser navigate TikTok live
- **Automatic Session Management**: Sessions are created and cleaned up automatically
- **Share Links**: Optionally creates shareable public links
- **Continuous Scrolling**: Agent keeps browsing until the task completes
- **Vision Mode**: Uses screenshot capability for better interaction

## Troubleshooting

### No livestream appearing
- Check that `mission_livestream_watcher.py` is running
- Verify your `BROWSER_USE_API_KEY` is set correctly
- Check the console for error messages

### Iframe not loading
- Some browsers block iframes - try a different browser
- Check browser console for security errors
- Verify the `liveUrl` is present in the mission record

### Session stays active too long
- The script automatically cleans up sessions after the task completes
- You can manually stop the watcher with Ctrl+C to clean up all sessions
