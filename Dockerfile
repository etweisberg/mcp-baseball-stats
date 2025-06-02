# Use Python 3.12 slim as base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache

# Install uv directly (most dependencies should be available in the base image)
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Copy the entire project
COPY mlb_stats_mcp /app/mlb_stats_mcp

# Install dependencies
RUN uv sync --frozen

# Copy .env file to the working directory
COPY .env /app/.env

# Create logs directory
RUN mkdir -p /app/logs

# Install the package in development mode system-wide
RUN uv pip install --system -e .

# Patch data for pybaseball
RUN uv run python mlb_stats_mcp/utils/scripts/data_download.py

# Expose port for HTTP transport
EXPOSE 8000

# Run the MCP server with HTTP transport
CMD ["python", "-m", "mlb_stats_mcp.server", "--http"]
