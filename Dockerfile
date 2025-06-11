FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    python3-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Create and activate virtual environment, install dependencies
RUN python3 -m venv .venv && \
    .venv/bin/pip install --upgrade pip && \
    .venv/bin/pip install -r requirements.txt

# Copy application code
COPY . .

# Set environment variables (optional, can be moved to railway.toml for Railway)
# Railway automatically injects PORT, no need to set it here
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
ENV GOOGLE_API_KEY=[REDACTED_GOOGLE_API_KEY]

# Health check command
# Use $PORT provided by Railway
HEALTHCHECK --interval=30s --timeout=60s --start-period=300s --retries=15 \
    CMD curl -f http://localhost:${PORT}/_stcore/health || exit 1

# Start Streamlit application from the virtual environment
# Use sh -c to ensure $PORT is expanded
CMD ["/bin/sh", "-c", "/app/.venv/bin/streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --logger.level debug"]
