import os
import streamlit as st
from pandasai_openai import OpenAI, AzureOpenAI
from pandasai_litellm import LiteLLM

def configure_llm(llm_option):
    """
    Configures and returns an LLM instance based on the user's selection.
    Handles API key loading from environment variables.
    """
    if llm_option == "GPT-4o":
        api_key = os.getenv("AZURE_OPENAI_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment_name = "deploy_gpt4o"
        if not api_key or not azure_endpoint:
            st.error("请在环境变量中设置 AZURE_OPENAI_KEY 和 AZURE_OPENAI_ENDPOINT")
            st.stop()
        return AzureOpenAI(
            model=f"azure/{deployment_name}", 
            deployment_name=deployment_name, 
            azure_endpoint=azure_endpoint, 
            api_token=api_key, 
            api_version="2024-02-01"
        )
    elif llm_option == "Gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        model_name = "gemini/gemini-1.5-pro-latest"
        if not api_key:
            st.error("请在环境变量中设置 GOOGLE_API_KEY")
            st.stop()
        os.environ["GEMINI_API_KEY"] = api_key
        return LiteLLM(model=model_name)
        
    elif llm_option == "Deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        api_base = os.getenv("DEEPSEEK_API_URL")
        model_name = "deepseek-chat"
        if not api_key or not api_base:
            st.error("请在环境变量中设置 DEEPSEEK_API_KEY 和 DEEPSEEK_API_URL")
            st.stop()
        return OpenAI(
            api_token=api_key, 
            api_base=api_base, 
            model=model_name, 
            is_chat_model=True
        )
    else:
        st.error("未知的模型选项！")
        st.stop() 