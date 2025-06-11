FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8501
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
ENV GOOGLE_API_KEY=[REDACTED_GOOGLE_API_KEY]

EXPOSE 8501

# 使用更简单的健康检查
HEALTHCHECK --interval=30s --timeout=60s --start-period=120s --retries=10 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 启动健康检查服务器
CMD /bin/bash -c "echo 'Starting Streamlit app.py with address $STREAMLIT_SERVER_ADDRESS and port $STREAMLIT_SERVER_PORT' && streamlit run --server.address=$STREAMLIT_SERVER_ADDRESS --server.port=$STREAMLIT_SERVER_PORT app.py" 