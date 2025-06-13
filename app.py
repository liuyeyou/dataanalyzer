import streamlit as st
import matplotlib
import os

# Set the backend to a non-interactive one BEFORE importing pyplot
matplotlib.use('AGG')

from src.ui import setup_page, setup_sidebar, display_chat_history, get_response_message, render_message
from src.data_processing import load_and_process_data
from src.llm_config import configure_llm
from src.agent_handler import create_agent, chat_with_agent
from src.intent_detector import get_intents

@st.cache_resource
def get_llm(llm_option):
    """Cached function to configure and return an LLM."""
    print(f"--- [CACHE MISS] Configuring LLM: {llm_option} ---")
    return configure_llm(llm_option)

def main():
    """Main function to run the Streamlit application."""
    setup_page()
    llm_option, uploaded_file = setup_sidebar()
    st.title("LLM 智能数据分析助手")

    data_container = st.container()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    display_chat_history()

    df = None
    if uploaded_file:
        df = load_and_process_data(uploaded_file, data_container)
    else:
        # Keep the container empty but present
        with data_container:
            pass
        st.info("请在左侧侧边栏上传一个 CSV 文件以开始分析。")

    if question := st.chat_input("输入你关于数据的问题..."):
        if df is None:
            st.warning("请先上传文件再提问。")
            st.stop()
        
        # Display user message in chat message container
        user_message = {"role": "user", "type": "text", "content": question}
        st.session_state.messages.append(user_message)
        with st.chat_message("user"):
            render_message(user_message)

        # Process and display assistant response
        with st.spinner("AI 正在思考中..."):
            try:
                llm = get_llm(llm_option)
                
                debug_container = st.expander("🐛 意图识别调试信息")
                intents = get_intents(question, llm, debug_container)
                
                st.info(f"🤖 已识别意图: {', '.join(intents)}")
                
                for intent in intents:
                    agent = create_agent(df, llm, intent=intent)
                    answer = chat_with_agent(agent, question)
                    
                    # Get the message dict and append to state
                    assistant_message = get_response_message(answer, intent)
                    st.session_state.messages.append(assistant_message)
                    
                    # Display the new message
                    with st.chat_message("assistant"):
                        render_message(assistant_message)
            
            except Exception as e:
                st.error("AI 分析失败，请检查数据格式或问题内容。")
                st.exception(e)
        # No st.rerun() needed, Streamlit handles it after input

if __name__ == "__main__":
    main() 