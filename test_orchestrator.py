#!/usr/bin/env python3
"""
Quick test script to verify the orchestrator setup.
Tests Convex connection and basic imports.
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        import asyncio
        print("  ✓ asyncio")
    except ImportError as e:
        print(f"  ✗ asyncio: {e}")
        return False
    
    try:
        from convex import ConvexClient
        print("  ✓ convex")
    except ImportError as e:
        print(f"  ✗ convex: {e}")
        return False
    
    try:
        from browser_use import Agent
        from browser_use.browser.profile import BrowserProfile
        print("  ✓ browser-use")
    except ImportError as e:
        print(f"  ✗ browser-use: {e}")
        return False
    
    return True


def test_environment():
    """Test that required environment variables are set."""
    print("\n🔍 Checking environment variables...")
    
    api_key = os.environ.get("BROWSER_USE_API_KEY")
    if api_key:
        print(f"  ✓ BROWSER_USE_API_KEY is set (ending in: ...{api_key[-8:]})")
    else:
        print("  ✗ BROWSER_USE_API_KEY is not set")
        print("    Set it with: export BROWSER_USE_API_KEY=your_key")
        return False
    
    return True


def test_convex_connection():
    """Test connection to Convex."""
    print("\n🔌 Testing Convex connection...")
    
    try:
        from convex import ConvexClient
        
        convex_url = "https://flexible-retriever-257.convex.cloud"
        client = ConvexClient(convex_url)
        
        print(f"  ✓ Connected to {convex_url}")
        
        # Try to query for active mission
        mission = client.query("missions:getLatestMission")
        print(f"  ✓ Successfully queried missions table")
        
        if mission:
            print(f"    Latest mission: {mission.get('prompt', 'N/A')[:50]}...")
            print(f"    Status: {mission.get('status')}")
        else:
            print("    No missions found yet")
        
        return True
    
    except Exception as e:
        print(f"  ✗ Convex connection failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("SwarmCast Orchestrator - Setup Test")
    print("="*60 + "\n")
    
    tests_passed = 0
    tests_total = 3
    
    if test_imports():
        tests_passed += 1
    
    if test_environment():
        tests_passed += 1
    
    if test_convex_connection():
        tests_passed += 1
    
    print("\n" + "="*60)
    print(f"Tests: {tests_passed}/{tests_total} passed")
    print("="*60 + "\n")
    
    if tests_passed == tests_total:
        print("✅ All tests passed! Ready to run orchestrator.py")
        print("\n💡 Next steps:")
        print("   1. Open http://localhost:3000 in your browser")
        print("   2. Create a mission in the UI")
        print("   3. Run: python orchestrator.py")
        return 0
    else:
        print("❌ Some tests failed. Fix the issues above before running the orchestrator.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
