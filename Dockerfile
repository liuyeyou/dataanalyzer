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
ENV PORT=8501
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
ENV GOOGLE_API_KEY=[REDACTED_GOOGLE_API_KEY]

EXPOSE 8501

# Health check command
HEALTHCHECK --interval=30s --timeout=60s --start-period=120s --retries=10 \
    CMD curl -f http://localhost:${PORT}/_stcore/health || exit 1

# Start Streamlit application from the virtual environment
CMD source .venv/bin/activate && streamlit run --server.address 0.0.0.0 --server.port $PORT --logger.level debug app.py 