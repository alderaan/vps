# VPS Architecture Diagram

```mermaid
graph TB
    %% Client Layer
    Client[Claude AI Client] -->|MCP Protocol<br/>Bearer Auth| Caddy[Caddy Reverse Proxy<br/>SSL/TLS]
    
    %% Web Layer
    Caddy -->|Port 8080| AIDev[AI Dev Server<br/>FastAPI + FastMCP]
    
    %% Application Layer
    AIDev -->|HTTP API| N8N[n8n Workflow Automation]
    AIDev -->|HTTP API<br/>Port 9000| HostAgent[HostAgent<br/>Host Service]
    
    %% Infrastructure Layer
    HostAgent -->|System Calls| Backup[Backup Scripts]
    HostAgent -->|Git Operations| GitRepo[Git Repository<br/>Workflow Storage]
    
    %% Automation Layer
    GitHub[GitHub Actions] -->|CI/CD Pipeline| Runner[Self-hosted Runner]
    Runner -->|Docker Commands| Docker[Docker Engine]
    
    %% Container Management
    Docker -->|Container Orchestration| Containers{Docker Containers}
    Containers --> AIDev
    Containers --> N8N
    Containers --> Registry[Container Registry]
    
    %% Security Layer
    UFW[UFW Firewall] -.->|Network Security| Caddy
    UFW -.->|Port Protection| HostAgent
    
    %% Styling
    classDef client fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef web fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef app fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef infra fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef container fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef security fill:#ffebee,stroke:#b71c1c,stroke-width:2px
    
    class Client client
    class Caddy web
    class AIDev,N8N,HostAgent app
    class Backup,GitRepo,GitHub,Runner infra
    class Docker,Containers,Registry container
    class UFW security
```

## Technology Stack Overview

### Core Technologies

1. **Docker** - Container runtime and orchestration
   - Manages all containerized services
   - Provides network isolation and service discovery
   - Enables consistent deployments

2. **FastAPI** - Modern Python web framework
   - Powers the AI Dev Server
   - Provides REST API endpoints
   - Automatic OpenAPI documentation

3. **FastMCP** - Model Context Protocol implementation
   - Enables AI agent integrations
   - Provides tool interface for Claude AI
   - Session management for stateful interactions

4. **Claude AI** - AI assistant platform
   - Connects via MCP protocol
   - Executes tools and workflows
   - Provides intelligent automation

5. **n8n** - Workflow automation platform
   - Visual workflow builder
   - API-driven automation
   - Integration with multiple services

6. **GitHub Actions** - CI/CD automation
   - Automated deployments on push
   - Self-hosted runner on VPS
   - Docker image building and registry push

7. **Caddy** - Web server and reverse proxy
   - Automatic HTTPS with Let's Encrypt
   - Request routing to services
   - Security headers and compression

8. **UFW** - Uncomplicated Firewall
   - Network security enforcement
   - Port access control
   - Service isolation

### Communication Flow

1. **Client → Caddy**: HTTPS requests with Bearer authentication
2. **Caddy → AI Dev Server**: Reverse proxy to localhost port 8080
3. **AI Dev Server → n8n**: HTTP API calls for workflow management
4. **AI Dev Server → HostAgent**: HTTP API calls for host operations
5. **HostAgent → System**: Direct system calls for backups and git operations
6. **GitHub Actions → Docker**: Automated deployment pipeline
7. **Docker → Services**: Container orchestration and networking