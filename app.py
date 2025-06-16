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
from src.prompts import ANALYSIS_PROMPT_TEMPLATE, GUIDANCE_PROMPT_TEMPLATE, SIMPLIFICATION_PROMPT_TEMPLATE

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

            # --- Step 1: Intent Detection ---
            with debug_container:
                st.write("Step 1: 识别用户意图...")
            with st.spinner("正在识别您的意图..."):
                intents = get_intents(question)
            st.info(f"🤖 已识别意图: {', '.join(intents)}")
            
            # --- Step 2: Simplify Query for Data Extraction ---
            with debug_container:
                st.write("Step 2: 简化用户问题用于数据提取...")
            with st.spinner("正在生成数据提取指令..."):
                simplification_prompt_str = SIMPLIFICATION_PROMPT_TEMPLATE.format(question=question)
                prompt_obj = BasePrompt()
                prompt_obj._resolved_prompt = simplification_prompt_str
                simplified_question = llm.call(prompt_obj)

            with debug_container:
                st.subheader("Step 2a: 简化后的提取问题")
                st.write(simplified_question)

            # --- Step 3: PandasAI Agent for Data Extraction ---
            with debug_container:
                st.write("Step 3: 使用 PandasAI Agent 提取分析所需数据...")
            with st.spinner("正在提取相关数据..."):
                extraction_agent = create_extraction_agent(df, llm)
                # Use the simplified question for the agent
                extracted_data_response = chat_with_agent(extraction_agent, simplified_question)

            # --- Response Handling Branch ---
            # Handle DataFrame for text analysis using isinstance
            if isinstance(extracted_data_response, DataFrameResponse):
                extracted_df = extracted_data_response.value
                
                # Check if the dataframe is empty after extraction
                if extracted_df.empty:
                    st.warning("数据提取步骤未能找到相关数据。请检查您的问题或上传的数据文件。")
                    st.stop()
                
                df_message = get_response_message(extracted_data_response, "dataframe")
                st.session_state.messages.append(df_message)
                with st.chat_message("assistant"):
                    render_message(df_message)

                # Continue to text analysis if intent is "string"
                if "string" in intents:
                    # --- Step 4: Generate Dynamic Analysis Guidance ---
                    with debug_container:
                        st.write("Step 4: 生成动态分析指导...")
                    with st.spinner("生成专属分析指令..."):
                        data_sample_csv = extracted_df.head().to_csv(index=False)
                        prompt_for_guidance = GUIDANCE_PROMPT_TEMPLATE.format(
                            question=question,
                            data_sample=data_sample_csv
                        )
                        guidance_prompt_obj = BasePrompt()
                        guidance_prompt_obj._resolved_prompt = prompt_for_guidance
                        analysis_guidance = llm.call(guidance_prompt_obj)

                    with debug_container:
                        st.subheader("Step 4a: 生成的分析指导")
                        st.write(analysis_guidance)

                    # --- Step 5: Generate Final Report using Guidance ---
                    with debug_container:
                        st.write("Step 5: 使用动态指导生成最终分析报告...")
                    
                    data_csv = extracted_df.to_csv(index=False)
                    
                    final_prompt_str = ANALYSIS_PROMPT_TEMPLATE.format(
                        query=question,
                        guidance=analysis_guidance,
                        data=data_csv
                    )
                    
                    prompt_obj = BasePrompt()
                    prompt_obj._resolved_prompt = final_prompt_str
                    
                    with st.spinner("正在生成最终分析报告..."):
                        analysis_report = llm.call(prompt_obj)
                    
                    text_message = get_response_message(analysis_report, "string")
                    st.session_state.messages.append(text_message)
                    with st.chat_message("assistant"):
                        render_message(text_message)

            # Handle Plot for chart display using isinstance
            elif isinstance(extracted_data_response, ChartResponse):
                with debug_container:
                    st.write("Step 4: 接收到图表响应，直接显示图表。")
                
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