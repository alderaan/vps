FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install curl for health checks and uv for fast dependency management
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY server.py ./

# Expose port
EXPOSE 8080

# Run the server
CMD ["uv", "run", "server.py"]