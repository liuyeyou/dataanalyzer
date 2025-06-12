import streamlit as st
import pandas as pd
import pandasai as pai
import os
from pandasai_openai import OpenAI, AzureOpenAI
from pandasai_litellm import LiteLLM

# 设置 pandas 显示所有列，防止数据被截断
pd.set_option('display.max_columns', None)

# --- 页面配置 ---
st.set_page_config(
    page_title="LLM 智能数据分析助手 v0.3(pandas-ai)", 
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- 注入自定义 CSS ---
hide_streamlit_style = """
<style>
/* 隐藏主菜单和页脚 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}

/* 隐藏 Streamlit 头部白条 */
[data-testid="stHeader"] {
    display: none;
}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 侧边栏 ---
with st.sidebar:
    st.subheader("设置")
    llm_option = st.selectbox("选择语言模型", ["GPT-4o", "Gemini", "Deepseek"], index=0)
    st.divider()
    st.subheader("加载数据")
    uploaded_file = st.file_uploader("选择 CSV 数据文件", type="csv")

# --- 主体内容 ---
st.title("LLM 智能数据分析助手 v0.3 (pandas-ai)")

# 创建一个容器来显示数据样本，确保它总是在顶部
data_container = st.container()

# 初始化或显示聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if uploaded_file is not None:
    # 使用 pandas 读取 CSV
    df = pd.read_csv(uploaded_file)
    
    # 在顶部的容器中显示数据信息
    with data_container:
        st.success(f'数据文件 "{uploaded_file.name}" 加载成功。')
        st.write("数据样本:", df.head())
        st.divider()

    # LLM配置
    if llm_option == "GPT-4o":
        api_key = os.getenv("AZURE_OPENAI_KEY")
        api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not api_key or not api_base:
            st.error("请在环境变量中设置 AZURE_OPENAI_KEY 和 AZURE_OPENAI_ENDPOINT")
            st.stop()
        llm = AzureOpenAI(
            deployment_name="deploy_gpt4o", # 假设您的 Azure 部署名称为 deploy_gpt4o
            azure_endpoint=api_base,
            api_token=api_key,
            api_version="2024-02-01" # 使用一个较新的稳定 API 版本
        )
    elif llm_option == "Gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            st.error("请在环境变量中设置 GOOGLE_API_KEY")
            st.stop()
        os.environ["GEMINI_API_KEY"] = api_key # LiteLLM aoturead
        llm = LiteLLM(model="gemini/gemini-1.5-pro-latest")
    elif llm_option == "Deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        api_base = os.getenv("DEEPSEEK_API_URL")
        if not api_key or not api_base:
            st.error("请在环境变量中设置 DEEPSEEK_API_KEY 和 DEEPSEEK_API_URL")
            st.stop()
        llm = OpenAI(api_token=api_key, api_base=api_base, model="deepseek-chat", is_chat_model=True)
    else:
        st.error("未知模型类型")
        st.stop()
        
    # 提问
    question = st.chat_input("输入你关于数据的问题...")
    if question:
        # 显示用户问题
        with st.chat_message("user"):
            st.markdown(question)
        # 记录用户问题
        st.session_state.messages.append({"role": "user", "content": question})

        with st.spinner("AI 正在思考中..."):
            try:
                # 使用 v3 Agent, 先将 pandas.DataFrame 包装成 pandasai.DataFrame
                pai_df = pai.DataFrame(df)
                # 构建指令 Prompt
                system_prompt = """

                你现在是一名专业的数据分析师，面前是一整份已加载完整的数据表格（DataFrame），请严格依据此表格作答，不得假设数据不完整或使用任何虚构信息。
                请严格遵循以下输出结构：

                📊【数据简述】

                - 涉及的字段有哪些？数据总共有多少天？涉及哪些关键收入项？
                - 当前问题关注的时间区间是哪几天？

                📉【数值分析】

                - 提供关键字段的对比数据（包括绝对值、差值、变化率）
                - 用简洁条目列出每一项变化，保留2位小数

                🔎【趋势与异常】

                - 指出趋势变化（增长、下降、震荡）
                - 识别异常点（骤升/骤降、缺失值、边缘值等）

                📌【原因推测】

                - 给出可能导致现象的业务/数据原因
                - 避免主观猜测，需基于数据合理分析


                📢【建议与行动】

                - 提出基于分析结果的业务建议、改进方向或后续验证方法

                请执行如下要求：
                1. 请用中文作答，逻辑清晰，语言专业，禁止使用“我认为”、“可能是因为”这类模糊表达。
                2. 禁止读取外部文件或进行任何形式的数据假设。
                """
                # 初始化 PandasAI Agent
                agent = pai.Agent(pai_df, config={
                    "llm": llm,
                    "enable_cache": False,
                    "verbose": True,
                    "conversational": False,
                    "use_sql": False, # 禁用 SQL 查询以避免内部 bug
                })

                final_prompt = f"{system_prompt}\n我的问题是：{question}"

                # 获取回答
                answer = agent.chat(final_prompt)

                # 显示AI回答
                with st.chat_message("assistant"):
                    st.markdown(answer)
                # 记录AI回答
                st.session_state.messages.append({"role": "assistant", "content": answer})

            except Exception as e:
                st.error("AI 分析失败，请检查数据格式或问题内容。")
                st.exception(e)  # 更直观显示完整报错信息
                st.stop()
else:
    st.info("请在左侧侧边栏上传一个 CSV 文件以开始分析。")
