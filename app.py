import streamlit as st
import datahelper

# Initialize session state for data loading and input fields
if "dataload" not in st.session_state:
    st.session_state.dataload = False
if "variable_input" not in st.session_state:
    st.session_state.variable_input = ""
if "question_input" not in st.session_state:
    st.session_state.question_input = ""

# Function to activate data loading and reset inputs
def activate_dataload():
    st.session_state.dataload = True
    st.session_state.variable_input = ""
    st.session_state.question_input = ""

# Configure the Streamlit page
st.set_page_config(
    page_title="数据分析助手 🤖", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# 隐藏 Streamlit 默认的菜单和页脚
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("LLM 智能数据分析助手")
st.divider()

# Sidebar configuration
st.sidebar.subheader("设置")
llm_option = st.sidebar.selectbox(
    "选择语言模型",
    ["Gemini", "Deepseek"],
    index=0
)
datahelper.set_llm(llm_option)

st.sidebar.divider()
st.sidebar.subheader("加载数据")
#st.sidebar.divider()

# File uploader for CSV files
loaded_file = st.sidebar.file_uploader("选择 CSV 数据文件", type="csv")
load_data_btn = st.sidebar.button(
    label="加载", on_click=activate_dataload, use_container_width=True
)

# Main layout
col_prework, col_dummy, col_interaction = st.columns([4, 1, 7])

# Note: Removed the custom health check here from previous attempts
# if st.experimental_get_query_params().get("_stcore") == ["health"]:
#     st.json(check_health())
#     st.stop()

if st.session_state.dataload:

    # Function to summarize data
    @st.cache_data(ttl=0)  # 设置缓存时间为0，每次都重新加载
    def summerize():
        loaded_file.seek(0)
        data_summary = datahelper.summerize_csv(filename=loaded_file)
        return data_summary

    data_summary = summerize()

    # Display data overview
    with col_prework:
        st.info("数据摘要")
        st.subheader("数据样本")
        st.write(data_summary["initial_data_sample"])
        st.divider()
        st.subheader("统计摘要")
        st.write(data_summary["essential_metrics"])
        st.divider()
        st.subheader("数据特征")
        st.write(data_summary["column_descriptions"])
        
    with col_dummy:
        st.empty()

    # Interaction section
    with col_interaction:
        st.info("交互分析")
        variable = st.text_input(label="请输入要分析的指标名称", key="variable_input")
        exemine_btn = st.button("分析")
        st.divider()

        # Function to explore a variable
        @st.cache_data(ttl=0)  # 设置缓存时间为0，每次都重新加载
        def explore_variable(data_file, variable):
            data_file.seek(0)
            dataframe = datahelper.get_dataframe(filename=data_file)
            st.bar_chart(data=dataframe, y=[variable])
            st.divider()

            data_file.seek(0)
            trend_response = datahelper.analyze_trend(
                filename=loaded_file, variable=variable
            )
            st.success(trend_response)
            return

        if variable or exemine_btn:
            explore_variable(data_file=loaded_file, variable=variable)

        free_question = st.text_input(label="请输入您想了解的数据问题", key="question_input")
        ask_btn = st.button(label="提问")
        st.divider()

        # Function to answer questions about the dataset
        @st.cache_data(ttl=0)  # 设置缓存时间为0，每次都重新加载
        def answer_question(data_file, free_question):
            data_file.seek(0)
            AI_response = datahelper.ask_question(
                filename=data_file, question=free_question
            )
            st.success(AI_response)
            return

        if free_question or ask_btn:
            answer_question(data_file=loaded_file, free_question=free_question)
