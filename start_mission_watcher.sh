#!/bin/bash
# Start the mission livestream watcher

echo "🚀 Starting Mission Livestream Watcher..."
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check for required environment variables
if [[ -z "$BROWSER_USE_API_KEY" ]]; then
    echo "❌ Error: BROWSER_USE_API_KEY not set"
    echo "   Get your API key from: https://cloud.browser-use.com/settings?tab=api-keys"
    echo "   Then run: export BROWSER_USE_API_KEY='your_key'"
    exit 1
fi

if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "❌ Error: OPENAI_API_KEY not set"
    echo "   Get your API key from: https://platform.openai.com/api-keys"
    echo "   Then run: export OPENAI_API_KEY='your_key'"
    exit 1
fi

# Run the watcher
python mission_livestream_watcher.py
