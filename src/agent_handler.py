import pandasai as pai
import os
# from src.parsers import SimpleOutputParser # No longer needed

def create_agent(df, llm, intent="string"):
    """
    Creates and configures a PandasAI agent with predefined prompts.
    Dynamically sets the agent's mode based on the user's intent.
    """
    pai_df = pai.DataFrame(df)
    
    # Define prompts for the agent
    system_prompt = """你现在是一名专业的数据分析师，请严格依据用户提供的 DataFrame 作答。

        **回答要求：**
        1.  **数据驱动：** 所有分析和结论必须基于表格中的数据，明确列出引用的数据列和数值。
        2.  **深度分析：** 进行必要的统计计算（如均值、增长率、占比），并解释计算过程和结果的业务含义。
        3.  **逻辑严谨：** 结论需有清晰的逻辑支撑，避免空泛或推测性的描述。
        4.  **结构化输出：** 如果是分析性回答，请严格按照以下 Markdown 格式进行回答，每个要点独占一行，不要使用 JSON 或字典格式。
        5.  **中文回答：** 全部使用中文。

        **分析性回答输出格式示例：**
        ```markdown
        📊【数据简述】
        - **核心字段:** [用于分析的关键字段列表]
        - **数据范围:** [分析所涉及的时间或其他维度范围]
        - **样本量:** [所分析的数据行数]

        📉【数值分析】
        - **[指标]变化:** [具体数值对比], 差值: [差值], 变化率: [变化率]

        🔎【趋势与异常】
        - **趋势变化:** [上升/下降/平稳]，并结合数据说明。
        - **异常点:** [是否存在异常数据点，如有请指出并分析]。
        ```"""
    columns_text = ", ".join(df.columns.tolist())
    dynamic_prompt = f"""
        你接下来将分析的表格包含以下字段：
        [{columns_text}]
        请尽可能理解用户的自然语言提问，自动匹配这些字段进行分析。
        字段可能为缩写、拼音或不常见表达，请灵活理解。优先匹配字段名称，其次匹配字段含义。
        """
    
    save_path = os.path.join(os.getcwd(), "exports/charts")
    os.makedirs(save_path, exist_ok=True)

    config = {
        "llm": llm,
        "enable_cache": False,
        "verbose": True,
        "use_sql": False,
        "custom_whitelisted_dependencies": ["pandas"],
        "prompt": system_prompt + "\n\n" + dynamic_prompt,
        "save_charts_path": save_path,
    }

    # Dynamically set agent mode based on intent
    if intent == "string":
        config["is_conversational_answer"] = True
        config["code_execution_config"] = {"enabled": False}
    else:
        # For 'plot' and 'dataframe', we need code generation.
        config["is_conversational_answer"] = False

    return pai.Agent(pai_df, config=config)

def chat_with_agent(agent, question: str):
    """
    Sends a question to the agent and returns the response.
    """
    return agent.chat(question) 