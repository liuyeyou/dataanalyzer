from flask import Flask
import requests
import time
import threading
import subprocess

app = Flask(__name__)

# 全局变量来跟踪 Streamlit 服务状态
streamlit_ready = False

def run_streamlit():
    """在后台运行 Streamlit"""
    subprocess.run(["streamlit", "run", "app.py", 
                   "--server.address", "0.0.0.0",
                   "--server.port", "8501"])

@app.route('/_stcore/health')
def health_check():
    """健康检查端点"""
    # 检查 Streamlit 是否在运行
    try:
        response = requests.get('http://localhost:8501')
        if response.status_code == 200:
            return {"status": "healthy"}, 200
    except:
        pass
    return {"status": "unhealthy"}, 503

def start_servers():
    """启动 Flask 和 Streamlit 服务器"""
    # 在后台线程中启动 Streamlit
    streamlit_thread = threading.Thread(target=run_streamlit)
    streamlit_thread.daemon = True
    streamlit_thread.start()
    
    # 启动 Flask 服务
    app.run(host='0.0.0.0', port=8502)

if __name__ == '__main__':
    start_servers() 