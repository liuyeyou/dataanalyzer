import streamlit as st
import matplotlib
import pandas as pd
import os

# Set the backend to a non-interactive one BEFORE importing pyplot
matplotlib.use("Agg")

from pandasai import SmartDataframe
from pandasai.core.response.chart import ChartResponse
from pandasai.core.response.dataframe import DataFrameResponse
from pandasai.core.prompts.base import BasePrompt

from src.ui import setup_page, setup_sidebar, display_chat_history, get_response_message, render_message
from src.data_processing import load_and_process_data
from src.llm_config import configure_llm
from src.agent_handler import create_extraction_agent, chat_with_agent
from src.intent_detector import get_intents
from src.prompts import ANALYSIS_PROMPT_TEMPLATE

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

    if "messages" not in st.session_state:
        st.session_state.messages = []

    display_chat_history()

    df = None
    if uploaded_file:
        df = load_and_process_data(uploaded_file, data_container)
    else:
        with data_container:
            pass
        st.info("请在左侧侧边栏上传一个 CSV 文件以开始分析。")

    if question := st.chat_input("输入你关于数据的问题..."):
        if df is None:
            st.warning("请先上传文件再提问。")
            st.stop()
        
        user_message = {"role": "user", "type": "text", "content": question}
        st.session_state.messages.append(user_message)
        with st.chat_message("user"):
            render_message(user_message)

        try:
            llm = get_llm(llm_option)
            debug_container = st.expander("🐛 操作日志")

            with debug_container:
                st.write("Step 1: 识别用户意图...")
            with st.spinner("正在识别您的意图..."):
                intents = get_intents(question)
            st.info(f"🤖 已识别意图: {', '.join(intents)}")
            
            # --- Final Pipeline ---
            
            # 1. PandasAI Agent for Data Extraction
            with debug_container:
                st.write("Step 2: 使用 PandasAI Agent 提取分析所需数据...")
            with st.spinner("正在提取相关数据..."):
                extraction_agent = create_extraction_agent(df, llm)
                extracted_data_response = chat_with_agent(extraction_agent, question)

            # --- Response Handling Branch ---
            # Handle DataFrame for text analysis using isinstance
            if isinstance(extracted_data_response, DataFrameResponse):
                extracted_df = extracted_data_response.value
                df_message = get_response_message(extracted_data_response, "dataframe")
                st.session_state.messages.append(df_message)
                with st.chat_message("assistant"):
                    render_message(df_message)

                # Continue to Step 3 for generating the text report
                if "string" in intents:
                    with debug_container:
                        st.write("Step 3: 直接调用 LLM 生成最终分析报告...")
                    
                    data_csv = extracted_df.to_csv(index=False)
                    
                    final_prompt_str = ANALYSIS_PROMPT_TEMPLATE.format(
                        query=question,
                        data=data_csv
                    )
                    
                    prompt_obj = BasePrompt()
                    prompt_obj._resolved_prompt = final_prompt_str
                    
                    with st.spinner("正在生成分析报告..."):
                        analysis_report = llm.call(prompt_obj)
                    
                    text_message = get_response_message(analysis_report, "string")
                    st.session_state.messages.append(text_message)
                    with st.chat_message("assistant"):
                        render_message(text_message)

            # Handle Plot for chart display using isinstance
            elif isinstance(extracted_data_response, ChartResponse):
                with debug_container:
                    st.write("Step 3: 接收到图表响应，直接显示图表。")
                
                chart_path = extracted_data_response.value
                plot_message = get_response_message(chart_path, "plot")
                st.session_state.messages.append(plot_message)
                with st.chat_message("assistant"):
                    render_message(plot_message)

            # Handle any other unexpected response
            else:
                st.error("数据提取失败或返回了不支持的响应类型。")
                st.exception(extracted_data_response)
                st.stop()

        except Exception as e:
            st.error("AI 分析失败，请检查数据格式或问题内容。")
            st.exception(e)

if __name__ == "__main__":
    main()