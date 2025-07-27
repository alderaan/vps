# DBT Docker Service

A containerized dbt (data build tool) environment for running data transformations on your VPS. This setup provides an on-demand dbt execution environment without requiring local installation.

## Overview

This service runs dbt-postgres in Docker containers that:
- Start on-demand when you run commands
- Automatically stop after completion
- Connect to the Supabase PostgreSQL database
- Mount your local dbt project for execution

## Configuration

### Docker Compose Setup

The service uses the following configuration:

- **Image**: `ghcr.io/dbt-labs/dbt-postgres:1.8.latest`
- **Container Name**: `dbt`
- **Network**: Connects to `supabase_default` network
- **Working Directory**: `/usr/app/dbt` inside container

### Volume Mounts

The service mounts two paths from your dbt project:

1. **Project Directory**: `${DBT_PROJECT_PATH}:/usr/app/dbt`
2. **Profiles Directory**: `${DBT_PROJECT_PATH}/profiles:/root/.dbt/`

Default path if `DBT_PROJECT_PATH` is not set: `~/dtc_backend/dtc_dbt`

## Environment Variables

Set these in a `.env` file in the same directory as docker-compose.yml:

```bash
# Path to your dbt project (optional, defaults to ~/dtc_backend/dtc_dbt)
DBT_PROJECT_PATH=/path/to/your/dbt/project
```

## Usage

### Basic Commands

```bash
# Run all models
docker compose run --rm dbt run

# Run specific models
docker compose run --rm dbt run --select model_name

# Test models
docker compose run --rm dbt test

# Generate documentation
docker compose run --rm dbt docs generate

# Debug connection
docker compose run --rm dbt debug
```

### Using Different Project Paths

Override the project path at runtime:

```bash
# Use a different dbt project
DBT_PROJECT_PATH=/home/david/another_project docker compose run --rm dbt run

# Or export it for the session
export DBT_PROJECT_PATH=/home/david/my_dbt_project
docker compose run --rm dbt run
```

### Common dbt Commands

```bash
# Compile SQL without running
docker compose run --rm dbt compile

# Run tests only
docker compose run --rm dbt test

# Run seeds
docker compose run --rm dbt seed

# List resources
docker compose run --rm dbt ls

# Check source freshness
docker compose run --rm dbt source freshness
```

## Prerequisites

1. **Docker and Docker Compose**: Must be installed on the system
2. **Supabase Network**: The `supabase_default` network must exist
3. **dbt Project**: A valid dbt project with:
   - `dbt_project.yml` configuration file
   - `profiles.yml` in the profiles directory
   - Models in the `models/` directory

## dbt Profile Configuration

Ensure your `profiles.yml` is configured to connect to your database. Example for Supabase:

```yaml
your_profile_name:
  target: dev
  outputs:
    dev:
      type: postgres
      host: db
      port: 5432
      user: postgres
      pass: "{{ env_var('POSTGRES_PASSWORD') }}"
      dbname: postgres
      schema: public
      threads: 4
```

## Network Configuration

The service connects to the `supabase_default` network, allowing it to:
- Access the Supabase PostgreSQL database using hostname `db`
- Communicate with other services on the same network

## Troubleshooting

### Container can't find dbt project

```bash
# Check if path is correctly mounted
docker compose run --rm dbt ls

# Verify the path exists
ls -la ~/dtc_backend/dtc_dbt  # or your DBT_PROJECT_PATH
```

### Database connection issues

```bash
# Test database connection
docker compose run --rm dbt debug

# Check if on correct network
docker network ls | grep supabase_default
```

### Permission issues

Ensure the dbt project directory and files are readable:
```bash
chmod -R 755 ~/dtc_backend/dtc_dbt
```

## Notes

- Containers run in foreground mode (`--rm` flag) and are removed after execution
- Each command starts a fresh container instance
- No persistent containers run in the background
- The dbt logs are output directly to your terminal

## Related Services

This dbt service is designed to work with:
- **Supabase**: Provides the PostgreSQL database
- **n8n**: Can trigger dbt runs as part of workflows
- **AI Dev Server**: Can orchestrate dbt operations

## License

Part of the VPS infrastructure management tools.