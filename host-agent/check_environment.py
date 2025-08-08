#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick pre-flight check for search functionality requirements.
"""
import subprocess
import shutil
from pathlib import Path

def check_ripgrep():
    """Check if ripgrep is installed."""
    print("Checking ripgrep...")
    try:
        result = subprocess.run(["rg", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split()[1]
            print(f"  [OK] Ripgrep {version} is installed")
            return True
        else:
            print(f"  [ERROR] Ripgrep error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("  [ERROR] Ripgrep not found")
        print("    Install with: brew install ripgrep")
        return False

def check_directories():
    """Check if required directories exist."""
    print("Checking directories...")
    base_path = Path("/Users/d.lucker/Code/vps")
    
    dirs_to_check = [
        base_path / "n8n-docs",
        base_path / "n8nio"
    ]
    
    all_exist = True
    for dir_path in dirs_to_check:
        if dir_path.exists() and dir_path.is_dir():
            file_count = len(list(dir_path.rglob("*")))
            print(f"  [OK] {dir_path} exists ({file_count} total files)")
        else:
            print(f"  [ERROR] {dir_path} not found")
            all_exist = False
    
    return all_exist

def check_python_deps():
    """Check if required Python packages are available."""
    print("Checking Python dependencies...")
    try:
        import fastapi
        print(f"  [OK] FastAPI {fastapi.__version__}")
    except ImportError:
        print("  [ERROR] FastAPI not installed")
        return False
    
    try:
        import pydantic
        print(f"  [OK] Pydantic {pydantic.__version__}")
    except ImportError:
        print("  [ERROR] Pydantic not installed")
        return False
    
    try:
        import httpx
        print(f"  [OK] HTTPX {httpx.__version__}")
    except ImportError:
        print("  [ERROR] HTTPX not installed")
        return False
    
    return True

def main():
    """Run all checks."""
    print("=" * 50)
    print("Environment Pre-flight Check")
    print("=" * 50)
    
    checks = [
        ("Ripgrep", check_ripgrep),
        ("Directories", check_directories),
        ("Python Dependencies", check_python_deps)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        print("-" * 20)
        results.append(check_func())
    
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    
    if all(results):
        print("[SUCCESS] All checks passed! Ready to test search functionality.")
        print("\nNext steps:")
        print("1. Run: python test_search_local.py")
        print("2. If that works, run the host agent and test the API")
    else:
        print("[FAILED] Some checks failed. Fix the issues above before proceeding.")
        print("\nCommon fixes:")
        print("- Install ripgrep: brew install ripgrep")
        print("- Install Python deps: uv sync")
        print("- Check that n8n-docs and n8nio directories exist")

if __name__ == "__main__":
    main()