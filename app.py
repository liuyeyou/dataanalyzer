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
from src.agent_handler import create_extraction_agent, create_processing_agent, chat_with_agent
from src.intent_detector import get_intents, get_analysis_type
from src.prompts import (
    ANALYSIS_PROMPT_TEMPLATE, 
    GUIDANCE_PROMPT_TEMPLATE, 
    SIMPLIFICATION_PROMPT_TEMPLATE, 
    PLOT_REQUEST_EXTRACTION_PROMPT_TEMPLATE,
    SIMPLE_ANSWER_PROMPT_TEMPLATE,
    DATAFRAME_REQUEST_EXTRACTION_PROMPT_TEMPLATE
)

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

            # --- Step 1: Intent & Analysis Type Detection ---
            with debug_container:
                st.write("Step 1: 识别用户意图和问题类型...")
            with st.spinner("正在识别您的意图..."):
                intents = get_intents(question)
            st.info(f"🤖 已识别意图: {', '.join(intents)}")
            
            analysis_type = None
            if "string" in intents:
                with st.spinner("正在判断问题类型..."):
                    analysis_type = get_analysis_type(question)
                st.info(f"🧐 问题类型: {analysis_type}")

            # --- ROUTING ---
            
            # Route 1: Deep Analysis Pipeline (highest priority)
            if analysis_type == 'deep_analysis':
                with debug_container:
                    st.write("Step 2: 检测到深度分析需求，启动完整分析流程...")
                
                # --- 2a. Data Extraction ---
                with st.spinner("正在生成数据提取指令..."):
                    simplification_prompt_str = SIMPLIFICATION_PROMPT_TEMPLATE.format(question=question)
                    prompt_obj = BasePrompt()
                    prompt_obj._resolved_prompt = simplification_prompt_str
                    simplified_question = llm.call(prompt_obj)
                with debug_container:
                    st.subheader("Step 2a: 简化后的提取问题")
                    st.write(simplified_question)

                with st.spinner("正在提取相关数据..."):
                    extraction_agent = create_extraction_agent(df, llm)
                    extracted_data_response = chat_with_agent(extraction_agent, simplified_question)
                
                if not isinstance(extracted_data_response, DataFrameResponse) or extracted_data_response.value.empty:
                    st.error("深度分析的数据提取步骤未能返回有效的表格数据。")
                    st.stop()
                
                extracted_df = extracted_data_response.value
                df_message = get_response_message(extracted_data_response, "dataframe")
                st.session_state.messages.append(df_message)
                with st.chat_message("assistant"):
                    render_message(df_message)

                # --- 2b. Textual Analysis (already part of this flow) ---
                with debug_container:
                    st.write("Step 3: 生成动态分析指导...")
                with st.spinner("生成专属分析指令..."):
                    data_sample_csv = extracted_df.head().to_csv(index=False)
                    prompt_for_guidance = GUIDANCE_PROMPT_TEMPLATE.format(question=question, data_sample=data_sample_csv)
                    guidance_prompt_obj = BasePrompt()
                    guidance_prompt_obj._resolved_prompt = prompt_for_guidance
                    analysis_guidance = llm.call(guidance_prompt_obj)
                
                with debug_container:
                    st.subheader("Step 3a: 生成的分析指导")
                    st.write(analysis_guidance)
                
                with st.spinner("正在生成最终分析报告..."):
                    data_csv = extracted_df.to_csv(index=False)
                    final_prompt_str = ANALYSIS_PROMPT_TEMPLATE.format(query=question, guidance=analysis_guidance, data=data_csv)
                    prompt_obj = BasePrompt()
                    prompt_obj._resolved_prompt = final_prompt_str
                    analysis_report = llm.call(prompt_obj)
                text_message = get_response_message(analysis_report, "string")
                st.session_state.messages.append(text_message)
                with st.chat_message("assistant"):
                    render_message(text_message)
                
                # --- 2c. Plotting (if also requested) ---
                if "plot" in intents:
                    with debug_container:
                        st.write("Step 4: 检测到绘图意图，在分析基础上生成图表...")
                    with st.spinner("正在提取绘图指令..."):
                        plot_request_prompt_str = PLOT_REQUEST_EXTRACTION_PROMPT_TEMPLATE.format(question=question)
                        prompt_obj = BasePrompt()
                        prompt_obj._resolved_prompt = plot_request_prompt_str
                        plot_question = llm.call(prompt_obj)
                    
                    with st.spinner("正在生成图表..."):
                        # Use the already extracted dataframe
                        chart_agent = create_processing_agent(extracted_df, llm)
                        response = chat_with_agent(chart_agent, plot_question)
                    
                    if isinstance(response, ChartResponse):
                        plot_message = get_response_message(response.value, "plot")
                        st.session_state.messages.append(plot_message)
                        with st.chat_message("assistant"):
                            render_message(plot_message)
                    else:
                        st.warning("图表生成失败，代理返回了非图表响应。")

            # Route 2: Direct Processing for all other cases
            else:
                with debug_container:
                    st.write("Step 2: 检测到直接处理需求，开始按序处理...")
                
                processing_agent = create_processing_agent(df, llm)
                
                # Sequentially handle plotting
                if "plot" in intents:
                    with debug_container:
                        st.write("  - 处理绘图请求...")
                    with st.spinner("正在提取绘图指令..."):
                        plot_request_prompt_str = PLOT_REQUEST_EXTRACTION_PROMPT_TEMPLATE.format(question=question)
                        prompt_obj = BasePrompt()
                        prompt_obj._resolved_prompt = plot_request_prompt_str
                        plot_question = llm.call(prompt_obj)
                    
                    if plot_question:
                        with st.spinner("正在生成图表..."):
                            response = chat_with_agent(processing_agent, plot_question)
                        if isinstance(response, ChartResponse):
                            plot_message = get_response_message(response.value, "plot")
                            st.session_state.messages.append(plot_message)
                            with st.chat_message("assistant"):
                                render_message(plot_message)
                        else:
                            st.warning("图表生成失败，代理返回了非图表响应。")

                # Sequentially handle dataframe calculation
                if "dataframe" in intents:
                    with debug_container:
                        st.write("  - 处理表格/计算请求...")

                    # Use the prompt from the central file
                    with st.spinner("正在提取表格计算指令..."):
                        dataframe_request_prompt_str = DATAFRAME_REQUEST_EXTRACTION_PROMPT_TEMPLATE.format(question=question)
                        prompt_obj = BasePrompt()
                        prompt_obj._resolved_prompt = dataframe_request_prompt_str
                        dataframe_question = llm.call(prompt_obj)

                    if dataframe_question:
                        with st.spinner("正在计算并生成表格..."):
                            response = chat_with_agent(processing_agent, dataframe_question)
                        if isinstance(response, DataFrameResponse):
                            df_message = get_response_message(response, "dataframe")
                            st.session_state.messages.append(df_message)
                            with st.chat_message("assistant"):
                                render_message(df_message)
                        else:
                             # If it fails to return a dataframe, it might return a string answer
                             text_message = get_response_message(str(response), "string")
                             st.session_state.messages.append(text_message)
                             with st.chat_message("assistant"):
                                 render_message(text_message)

                # Handle simple lookups that are not plots or dataframes
                if "string" in intents and analysis_type == 'simple_lookup' and not ("plot" in intents or "dataframe" in intents):
                    with debug_container:
                        st.write("  - 处理简单问答请求...")
                    with st.spinner("正在生成答案..."):
                        response = chat_with_agent(processing_agent, question)
                        text_message = get_response_message(str(response), "string")
                        st.session_state.messages.append(text_message)
                        with st.chat_message("assistant"):
                            render_message(text_message)

        except Exception as e:
            st.error("AI 分析失败，请检查数据格式或问题内容。")
            st.exception(e)

if __name__ == "__main__":
    main()