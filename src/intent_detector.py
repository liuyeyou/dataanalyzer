import pandas as pd
import pandasai as pai
from typing import Any, List
import json
import streamlit as st
from pandasai.smart_dataframe import SmartDataframe

def get_intents(query: str, llm: Any, debug_container=None) -> list:
    try:
        #empty_df = pd.DataFrame()
        dummy_df = SmartDataframe(pd.DataFrame({"temp_column": [0]}))
        agent = pai.Agent(dummy_df, config={
            "llm": llm,
            "verbose": False,
            "is_conversational_answer": True, # ✅ 强制用对话模式
            "code_execution_config": {          # ✅ 显式禁用 SQL/Python 执行
                "enabled": False
            }
        })

        prompt = f"""
Analyze the user's query to identify all intents. The user query is: "{query}"

Respond with a single-line JSON object containing boolean flags for 'plot', 'dataframe', and 'string'. Do not add any explanation.

For example:
- For "show me a chart of sales", respond: {{"plot": true, "dataframe": false, "string": false}}
- For "give me the data and a summary", respond: {{"plot": false, "dataframe": true, "string": true}}
- For "why did numbers drop? show me the data and a graph", respond: {{"plot": true, "dataframe": true, "string": true}}

Your response must be only the JSON object.
"""

        raw = agent.chat(prompt, output_type="string")
        # Clean the raw response to get only the JSON part
        raw_cleaned = str(raw).strip()
        if "```json" in raw_cleaned:
            raw_cleaned = raw_cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_cleaned:
            raw_cleaned = raw_cleaned.split("```")[1].strip()

        intents = []
        try:
            parsed_json = json.loads(raw_cleaned)
            if parsed_json.get("plot"):
                intents.append("plot")
            if parsed_json.get("dataframe"):
                intents.append("dataframe")
            if parsed_json.get("string"):
                intents.append("string")
        except (json.JSONDecodeError, AttributeError):
            # Fallback for non-JSON or unexpected format
            raw_lower = raw_cleaned.lower()
            if "plot: yes" in raw_lower or '"plot": true' in raw_lower:
                intents.append("plot")
            if "dataframe: yes" in raw_lower or '"dataframe": true' in raw_lower:
                intents.append("dataframe")
            if "string: yes" in raw_lower or '"string": true' in raw_lower:
                intents.append("string")

        final_intents = intents or ["string"]

        if debug_container:
            with debug_container:
                st.write("**LLM 原始返回:**")
                st.code(raw)
                st.write("**解析后意图:**")
                st.code(str(final_intents))
        else:
            print(f"[INTENT DEBUG] LLM原始返回: {raw}")
            print(f"[INTENT DEBUG] 解析后意图: {final_intents}")

        return final_intents
    except Exception as e:
        if debug_container:
            with debug_container:
                st.error("意图识别时发生错误。")
                st.exception(e)
        return ["string"]