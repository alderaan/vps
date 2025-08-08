# Testing Guide for n8n Search Functionality

This guide helps you test the search functionality locally before deploying to the VPS.

## Quick Start

1. **Pre-flight check** (run this first):
   ```bash
   python check_environment.py
   ```

2. **Test core search logic** (no server needed):
   ```bash
   python test_search_local.py
   ```

3. **Test API endpoints** (requires running server):
   ```bash
   # Terminal 1 - Start host agent
   cp .env.example .env
   uv sync
   uv run python src/host_agent/main.py
   
   # Terminal 2 - Run API tests
   python test_api_local.py
   ```

## What Each Test Does

### `check_environment.py`
- ✅ Verifies ripgrep is installed
- ✅ Checks n8n-docs and n8nio directories exist  
- ✅ Confirms Python dependencies are available
- **Run this first** - fixes most common issues

### `test_search_local.py` 
- Tests search functionality directly (no HTTP/auth)
- Tests file retrieval
- Tests security (path traversal protection)
- **Safe to run** - no server or network required

### `test_api_local.py`
- Tests HTTP API endpoints
- Tests authentication 
- Tests error handling
- **Requires** host agent server running

## Expected Results

All tests should pass with output like:
```
✓ Ripgrep 14.0.3 is installed
✓ /Users/d.lucker/Code/n8n-docs exists (1250 total files)
✓ /Users/d.lucker/Code/n8nio exists (5430 total files)
✓ Found 45 matches
✓ Results in 12 files
✓ Path traversal correctly blocked
```

## Common Issues & Fixes

### "Ripgrep not found"
```bash
brew install ripgrep
```

### "Directory not found"
Check that you have these directories:
- `/Users/d.lucker/Code/n8n-docs`
- `/Users/d.lucker/Code/n8nio`

### "Cannot connect to host agent"
Make sure the server is running:
```bash
uv run python src/host_agent/main.py
```

### "Invalid token"
Check your `.env` file has:
```
BEARER_TOKEN=test-token-123
```

## What Could Still Fail on VPS

Even if local tests pass, these could fail on VPS:
1. **Different paths** - VPS uses `/home/david/vps/` instead of `/Users/d.lucker/Code/`
2. **Permissions** - VPS service runs as specific user
3. **Docker networking** - AI dev server connects via `host.docker.internal:9000`
4. **Environment variables** - Different token values

## Ready for VPS Deployment?

If all local tests pass, the implementation is sound. VPS issues will likely be:
- Configuration (paths, tokens)
- Infrastructure (networking, permissions)
- Not code logic

Deploy with confidence! 🚀