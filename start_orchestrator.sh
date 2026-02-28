#!/bin/bash

# SwarmCast Orchestrator Quick Start Script
# Sets up environment and runs the orchestrator

echo "🐝 Starting SwarmCast Orchestrator..."
echo ""

# Set environment variables
export BROWSER_USE_API_KEY="bu_ydoAyk34xD4xLVAdvgAC-SGA0Egwh6sXTQ5TRRWn-DM"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Run the orchestrator
.venv/bin/python orchestrator.py
