import streamlit as st
import pandas as pd
import os
from pandasai.core.response.dataframe import DataFrameResponse

def setup_page():
    """Configures the Streamlit page and injects custom CSS."""
    st.set_page_config(
        page_title="LLM智能数据分析助手",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    [data-testid="stHeader"] {display: none;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def setup_sidebar():
    """Sets up the sidebar and returns user selections."""
    with st.sidebar:
        st.subheader("设置")
        llm_option = st.selectbox("选择语言模型", ["GPT-4o", "Gemini", "Deepseek"], index=0)
        st.divider()
        st.subheader("加载数据")
        uploaded_file = st.file_uploader("选择 CSV 数据文件", type="csv")
    return llm_option, uploaded_file

def display_chat_history():
    """Initializes and displays the chat history from session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            render_message(message)

def render_message(message):
    """Renders a single message based on its type."""
    if message.get("type") == "image":
        st.image(message["content"], caption="历史图表")
    elif message.get("type") == "table":
        st.dataframe(pd.DataFrame(message["content"]))
    else:
        st.markdown(message["content"])

def get_response_message(answer, intent):
    """Converts an agent's answer into a message dictionary based on intent."""
    # 0. Handle the new composite dictionary response first
    if isinstance(answer, dict) and answer.get("type") == "dict":
        return {"role": "assistant", "type": "multi", "content": answer["value"]}
        
    # 1. Plot response
    if intent == "plot" and isinstance(answer, str) and answer.endswith('.png') and os.path.exists(answer):
        return {"role": "assistant", "type": "image", "content": answer}
    # 2. DataFrame response
    elif intent == "dataframe" and isinstance(answer, DataFrameResponse):
        return {"role": "assistant", "type": "table", "content": answer.value.to_dict()}
    # 3. String response
    elif intent == "string" and isinstance(answer, str):
        return {"role": "assistant", "type": "text", "content": answer}
    # 4. Fallback for other types or mismatches
    else:
        # Handle cases where intent doesn't match answer type gracefully
        if isinstance(answer, DataFrameResponse):
            return {"role": "assistant", "type": "table", "content": answer.value.to_dict()}
        elif isinstance(answer, str) and answer.endswith('.png') and os.path.exists(answer):
            return {"role": "assistant", "type": "image", "content": answer}
        else:
            return {"role": "assistant", "type": "text", "content": str(answer)} 