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
ENV PORT=8502
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
ENV GOOGLE_API_KEY=[REDACTED_GOOGLE_API_KEY]
ENV FLASK_ENV=production

EXPOSE 8501 8502

# 使用更简单的健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8502/_stcore/health || exit 1

# 启动健康检查服务器
CMD ["python", "health_server.py"]

# 使用shell形式的CMD以便能使用环境变量
CMD echo "Starting Streamlit..." && \
    echo "Server Address: $STREAMLIT_SERVER_ADDRESS" && \
    echo "Server Port: $STREAMLIT_SERVER_PORT" && \
    streamlit run --server.address=$STREAMLIT_SERVER_ADDRESS --server.port=$STREAMLIT_SERVER_PORT app.py 