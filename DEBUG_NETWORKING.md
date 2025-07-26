# DEBUG NETWORKING ISSUE

## Problem
- ai-dev-server (Docker) tries to connect to HostAgent via `http://host.docker.internal:9000`
- HostAgent is running on VPS at `0.0.0.0:9000` (confirmed in logs)
- ai-dev-server logs show "Starting n8n backup via HostAgent" and "Calling HostAgent backup endpoint..." but no request reaches HostAgent
- No errors in ai-dev-server, just hangs after "Calling HostAgent backup endpoint..."

## Tests to Run on VPS

### 1. Test Container Connectivity
```bash
cd /home/david/docker-compose/ai-dev-server
docker exec ai-dev-server curl -v http://host.docker.internal:9000/health
```

### 2. Test Host Resolution from Container
```bash
docker exec ai-dev-server nslookup host.docker.internal
docker exec ai-dev-server ping -c 3 host.docker.internal
```

### 3. Test Direct Connection to HostAgent
```bash
curl -v http://localhost:9000/health
curl -v http://127.0.0.1:9000/health
curl -v http://0.0.0.0:9000/health
```

### 4. Check Container Network
```bash
docker exec ai-dev-server ip route
docker exec ai-dev-server cat /etc/hosts | grep host.docker.internal
```

### 5. Test HostAgent Backup Endpoint Directly
```bash
curl -X POST http://localhost:9000/backup/n8n \
  -H "Authorization: Bearer $HOST_AGENT_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -v
```

### 6. Check if HostAgent is listening on all interfaces
```bash
sudo netstat -tlnp | grep 9000
sudo ss -tlnp | grep 9000
```

## Expected Findings
- host.docker.internal should resolve to host IP
- HostAgent should be accessible from container
- If not, the issue is likely Docker networking or HostAgent binding

## Potential Fixes
1. If HostAgent only binds to localhost, change it to bind to 0.0.0.0
2. If host.docker.internal doesn't work, add explicit host IP to extra_hosts in docker-compose
3. Check firewall rules blocking container -> host communication