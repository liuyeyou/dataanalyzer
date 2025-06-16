import os
from typing import List
import streamlit as st
from pandasai_litellm import LiteLLM
from pandasai.core.prompts.base import BasePrompt
from src.prompts import ANALYSIS_TYPE_PROMPT_TEMPLATE

# BasePrompt is designed to be subclassed, not instantiated directly for our use case.
# We create a simple subclass that takes a raw text string as its template.
class TextPrompt(BasePrompt):
    def __init__(self, text: str):
        self.template = text
        super().__init__()

def get_intents(query: str) -> list:
    try:
        # Instantiate Gemini LLM via LiteLLM for intent detection
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            error_message = "GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set."
            # if debug_container:
            #     with debug_container:
            #         st.error(error_message)
            raise ValueError(error_message)

        llm = LiteLLM(model="gemini/gemini-1.5-pro-latest", api_key=api_key)
        
        # We should not use an Agent for a simple intent detection task.
        # The Agent's purpose is to generate and execute code, which is not what we need here.
        # Instead, we can call the LLM directly.
        
        prompt_text = f"""
你是一个意图识别助手。请根据用户问题，判断其意图，可能有多种（用英文逗号分隔，顺序为 plot, dataframe, string）。

意图定义如下：
- plot: 用户希望生成图表（如柱状图、折线图、饼图等）
- dataframe: 用户希望获取表格、列、或明细数据
- string: 用户希望获得文字总结、解释或简要分析

请判断以下问题的意图，不需要解释，直接输出意图关键词：
问题：{query}
"""
        # The llm.call() method requires a Prompt object. We use our custom TextPrompt class.
        prompt = TextPrompt(prompt_text)
        raw_content = llm.call(prompt)
        
        # Always print to console for debugging
        print(f"[INTENT DEBUG] LLM原始返回: {raw_content}")
        
        intents = [i.strip() for i in str(raw_content).lower().split(",") if i.strip() in {"plot", "dataframe", "string"}]
        final_intents = intents or ["string"]

        print(f"[INTENT DEBUG] 解析后意图: {final_intents}")

        # Optionally display in Streamlit UI
        # if debug_container:
        #     with debug_container:
        #         st.write("**LLM 原始返回:**")
        #         st.code(raw_content)
        #         st.write("**解析后意图:**")
        #         st.code(str(final_intents))

        return final_intents
    except Exception as e:
        # if debug_container:
        #     with debug_container:
        #         st.error("意图识别时发生错误。")
        #         st.exception(e)
        # Also log to console on error
        print(f"Error during intent detection: {e}")
        return ["string"]

def get_analysis_type(query: str) -> str:
    """
    Classifies a 'string' type query as either 'simple_lookup' or 'deep_analysis'.
    """
    try:
        # Re-use the same LLM setup as get_intents
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.")

        llm = LiteLLM(model="gemini/gemini-1.5-pro-latest", api_key=api_key)
        
        prompt_text = ANALYSIS_TYPE_PROMPT_TEMPLATE.format(question=query)
        
        prompt = TextPrompt(prompt_text) # Reusing TextPrompt class from this file
        raw_content = llm.call(prompt)
        
        print(f"[ANALYSIS_TYPE DEBUG] LLM原始返回: {raw_content}")
        
        analysis_type = str(raw_content).strip().lower()
        
        if analysis_type in {"simple_lookup", "deep_analysis"}:
            final_type = analysis_type
        else:
            # Default to deep_analysis to be safe and provide more info
            final_type = "deep_analysis"
            
        print(f"[ANALYSIS_TYPE DEBUG] 解析后类型: {final_type}")

        return final_type
    except Exception as e:
        print(f"Error during analysis type detection: {e}")
        # Default to deep_analysis in case of error
        return "deep_analysis"