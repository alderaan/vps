# DEBUG NETWORKING ISSUE - RESOLVED

## Problem Identified
- ai-dev-server (Docker) could resolve `host.docker.internal` but HTTP requests hung
- HostAgent backup endpoint works perfectly when accessed directly from host
- Docker bridge networking was blocking container→host traffic on port 9000

## Solution Applied
1. Added explicit IP mapping to docker-compose.yml:
   ```yaml
   extra_hosts:
     - "host.docker.internal:host-gateway"
     - "hostagent.local:153.92.4.240"
   ```

2. Updated ai-dev-server code to use `http://hostagent.local:9000` instead of `http://host.docker.internal:9000`

## Test After Fix
```bash
cd /home/david/docker-compose/ai-dev-server
docker-compose down
docker-compose up -d

# Wait for container to start, then test
docker exec ai-dev-server curl -v http://hostagent.local:9000/health

# Test the backup endpoint from container
docker exec ai-dev-server curl -X POST http://hostagent.local:9000/backup/n8n \
  -H "Authorization: Bearer $HOST_AGENT_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -v
```

## Expected Result
- Container should now successfully connect to HostAgent
- n8n backup should complete successfully via MCP tool