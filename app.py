import streamlit as st
import pandas as pd
import pandasai as pai
import os
import matplotlib
import re

# Set the backend to a non-interactive one BEFORE importing pyplot
matplotlib.use('AGG')

from pandasai_openai import OpenAI, AzureOpenAI
from pandasai_litellm import LiteLLM
from pandasai.core.response.dataframe import DataFrameResponse

# 设置 pandas 显示所有列，防止数据被截断
pd.set_option('display.max_columns', None)

# --- 页面配置 ---
st.set_page_config(
    page_title="LLM智能数据分析助手", 
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
st.title("LLM 智能数据分析助手")


# 创建一个容器来显示数据样本，确保它总是在顶部
data_container = st.container()

# 初始化或显示聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("type") == "image":
            st.image(message["content"], caption="历史图表")
        elif message.get("type") == "table":
            st.dataframe(pd.DataFrame(message["content"]))
        else:
            st.markdown(message["content"])

if uploaded_file is not None:
    # 使用 pandas 读取 CSV
    df = pd.read_csv(uploaded_file)

    # 清理列名，去除特殊字符
    def clean_column_names(df):
        new_columns = {}
        for col in df.columns:
            # 使用正则表达式去除所有非字母、非数字、非中文字符，下划线除外
            new_col = re.sub(r'[^\w\u4e00-\u9fa5]', '', str(col))
            new_columns[col] = new_col
        df.rename(columns=new_columns, inplace=True)
        return df

    df = clean_column_names(df)
    
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

                # 定义系统 Prompt
                system_prompt = """你现在是一名专业的数据分析师，请严格依据用户提供的 DataFrame 作答。

**回答要求：**
1.  **数据驱动：** 所有分析和结论必须基于表格中的数据，明确列出引用的数据列和数值。
2.  **深度分析：** 进行必要的统计计算（如均值、增长率、占比），并解释计算过程和结果的业务含义。
3.  **逻辑严谨：** 结论需有清晰的逻辑支撑，避免空泛或推测性的描述。
4.  **结构化输出：** 请严格按照以下 Markdown 格式进行回答，每个要点独占一行，不要使用 JSON 或字典格式。
5.  **中文回答：** 全部使用中文。

**输出格式：**
```markdown
📊【数据简述】
- **核心字段:** [用于分析的关键字段列表]
- **数据范围:** [分析所涉及的时间或其他维度范围]
- **样本量:** [所分析的数据行数]

📉【数值分析】
- **[指标]变化:** [具体数值对比], 差值: [差值], 变化率: [变化率]
- **[收入构成]分析:** [各部分收入的占比及变化情况]

🔎【趋势与异常】
- **趋势变化:** [上升/下降/平稳]，并结合数据说明。
- **异常点:** [是否存在异常数据点，如有请指出并分析]。

📌【原因推测】
- **主要原因:** [基于数据分析，推断导致变化的核心原因，例如：XX收入下降是总收入降低的主要原因]。
- **次要原因:** [其他影响因素]。

📢【建议与行动】
- **业务建议:** [针对分析结果，提出具体的业务操作建议]。
- **改进方向:** [可以从哪些方面着手改进]。
- **后续验证:** [如何跟踪和验证建议措施的效果]。
```"""
                save_path = os.path.join(os.getcwd(), "exports/charts")
                os.makedirs(save_path, exist_ok=True)  # 自动创建目录（如不存在）
                # 初始化 PandasAI Agent
                agent = pai.Agent(pai_df, config={
                    "llm": llm,
                    "enable_cache": False,
                    "verbose": True,
                    "conversational": False,
                    "use_sql": False, # 禁用 SQL 查询以避免内部 bug
                    "custom_whitelisted_dependencies": ["pandas"],
                    "prompt": system_prompt,
                     "save_charts_path": save_path,  # ✅ 新增：图表输出目录
                })

                # 获取回答
                answer = agent.chat(question)

                # 显示AI回答
                with st.chat_message("assistant"):
                    # 1. 图表展示（本地 PNG 路径）
                    if isinstance(answer, str) and answer.endswith('.png') and os.path.exists(answer):
                        # 如果是 PandasAI 生成的图表路径，显示图片
                        st.image(answer, caption="AI 生成的图表")
                        # 保存消息用于回显，不用写成 markdown
                        st.session_state.messages.append({
                            "role": "assistant",
                            "type": "image",
                            "content": answer
                        })

                    # 2. 表格结果（DataFrameResponse 类型）
                    elif isinstance(answer, DataFrameResponse):
                        df_to_display = answer.value
                        st.dataframe(df_to_display)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "type": "table",
                            "content": df_to_display.to_dict()
                        })

                    # 3. 普通字符串文本（分析结果、自然语言解释等）
                    elif isinstance(answer, str):
                        st.markdown(answer)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "type": "text",
                            "content": answer
                        })

                    # 4. 兜底处理（未知类型）
                    else:
                        st.markdown(str(answer))
                        st.session_state.messages.append({
                            "role": "assistant",
                            "type": "text",
                            "content": str(answer)
                        })


            except Exception as e:
                st.error("AI 分析失败，请检查数据格式或问题内容。")
                st.exception(e)  # 更直观显示完整报错信息
                st.stop()
else:
    st.info("请在左侧侧边栏上传一个 CSV 文件以开始分析。")
