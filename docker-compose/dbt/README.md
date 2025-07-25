# 🐳 Dockerized dbt

A lightweight, on-demand dbt environment that runs locally on your VPS. This setup allows you to execute dbt commands without installing dbt locally, using Docker containers that spin up when needed and shut down after completion.

## 🚀 Features

- **On-demand execution**: Containers start when you run commands and stop when finished
- **No persistent containers**: Clean, resource-efficient operation
- **Flexible project paths**: Specify any dbt project directory at runtime
- **PostgreSQL support**: Configured for dbt-postgres adapter
- **Network integration**: Connects to existing Supabase network

## 📋 Prerequisites

- Docker and Docker Compose installed
- Access to the `supabase_default` network
- A `.env` file with your dbt configuration

## 🎯 Usage

### Basic Commands

Run dbt commands by specifying your project directory:

```bash
# Run all models in your project
DBT_PROJECT_PATH=~/your_dbt_project docker compose run --rm dbt run

# Run a specific model
DBT_PROJECT_PATH=~/your_dbt_project docker compose run --rm dbt run --select your_model_name

# Test your models
DBT_PROJECT_PATH=~/your_dbt_project docker compose run --rm dbt test

# Generate documentation
DBT_PROJECT_PATH=~/your_dbt_project docker compose run --rm dbt docs generate
```

### Examples

**Running all models in your project:**
```bash
docker compose run --rm dbt run
```

**Running with a different project path:**
```bash
DBT_PROJECT_PATH=~/another_dbt_project docker compose run --rm dbt run
```

**Running a specific model:**
```bash
DBT_PROJECT_PATH=~/another_dbt_project docker compose run --rm dbt run --select your_model_name
```

## ⚙️ Configuration

The setup uses the `ghcr.io/dbt-labs/dbt-postgres:1.8.latest` image and mounts your dbt project directory into the container. The `DBT_PROJECT_PATH` environment variable defaults to `~/dtc_dbt` if not specified.

## 🔧 Environment Setup

Create a `.env` file in the same directory as your `docker-compose.yml` with your dbt configuration:

```bash
# Example .env file
DBT_PROJECT_PATH=~/your_default_dbt_project
# Add other environment variables as needed
```

## 🌐 Network Configuration

This setup connects to the `supabase_default` network. Ensure this network exists in your Docker environment before running commands.

## 📝 Notes

- Containers run in non-detached mode and stop automatically after command completion
- Each command starts a fresh container instance
- Your dbt profiles are mounted from the project directory
- The working directory inside the container is `/usr/app/dbt`