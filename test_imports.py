#!/usr/bin/env python3
"""Test script to check imports"""

import sys
sys.path.insert(0, '.')

print("Testing imports...")

try:
    print("1. Importing agent.tools...")
    from agent import tools
    print("   ✓ agent.tools imported")

    print("2. Checking execute_tool...")
    if hasattr(tools, 'execute_tool'):
        print("   ✓ execute_tool exists")
    else:
        print("   ✗ execute_tool NOT FOUND")
        print(f"   Available: {dir(tools)}")

    print("3. Importing agent.prompts...")
    from agent import prompts
    print("   ✓ agent.prompts imported")

    print("4. Importing agent.brain...")
    from agent import brain
    print("   ✓ agent.brain imported")

    print("5. Importing from agent package...")
    from agent import FinaiAgent, run_agent
    print("   ✓ FinaiAgent, run_agent imported")

    print("\n✅ All imports successful!")

except Exception as e:
    print(f"\n❌ Import error: {e}")
    import traceback
    traceback.print_exc()
