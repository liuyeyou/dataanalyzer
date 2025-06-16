import streamlit as st
import pandas as pd
import os

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
        content = str(message.get("content", ""))

        # Strip the markdown code block fences if they exist
        if content.startswith("```markdown"):
            content = content.replace("```markdown", "", 1).strip()
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0].strip()

        # Now render the cleaned content
        st.markdown(content, unsafe_allow_html=True)

def get_response_message(answer, intent):
    """Converts an agent's answer into a message dictionary based on intent."""
        
    # 1. Plot response
    if intent == "plot":
        # The 'answer' is now the file path string
        return {"role": "assistant", "type": "image", "content": answer}
        
    # 2. DataFrame response
    elif intent == "dataframe":
        # The 'answer' is now the DataFrame response object from pandasai
        return {"role": "assistant", "type": "table", "content": answer.value.to_dict()}
        
    # 3. String response
    elif intent == "string":
        # The 'answer' is a string
        return {"role": "assistant", "type": "text", "content": answer}
        
    # 4. Fallback for any other case
    else:
        return {"role": "assistant", "type": "text", "content": str(answer)}