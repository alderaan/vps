#!/usr/bin/env python3
"""
Run all tests in sequence.
"""
import asyncio
import subprocess
import sys
from pathlib import Path

def run_sync_test(script_name: str) -> bool:
    """Run a synchronous test script."""
    print(f"\n{'='*60}")
    print(f"Running {script_name}")
    print('='*60)
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=Path(__file__).parent
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running all n8n search tests...")
    
    tests = [
        "check_environment.py",
        "test_search_local.py"
    ]
    
    results = []
    for test in tests:
        success = run_sync_test(test)
        results.append((test, success))
        if not success:
            print(f"\n❌ {test} failed - stopping here")
            print("\nFix the issues above before proceeding to API tests.")
            break
    else:
        print(f"\n{'='*60}")
        print("🎉 All core tests passed!")
        print('='*60)
        print("\nNext steps:")
        print("1. Start the host agent in another terminal:")
        print("   uv run python src/host_agent/main.py")
        print("2. Run API tests:")
        print("   python test_api_local.py")
        print("\nIf API tests also pass, you're ready for VPS deployment! 🚀")
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print('='*60)
    for test, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test}")

if __name__ == "__main__":
    main()