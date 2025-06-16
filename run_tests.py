import os
import pandas as pd
from dotenv import load_dotenv

from pandasai.core.response.chart import ChartResponse
from pandasai.core.response.dataframe import DataFrameResponse
from pandasai.core.prompts.base import BasePrompt

# Load environment variables from .env file
load_dotenv()

# Ensure the correct backend is set for matplotlib before any other imports
import matplotlib
matplotlib.use("Agg")

from src.llm_config import configure_llm
from src.intent_detector import get_intents
from src.agent_handler import create_extraction_agent, chat_with_agent
from src.prompts import ANALYSIS_PROMPT_TEMPLATE, GUIDANCE_PROMPT_TEMPLATE, SIMPLIFICATION_PROMPT_TEMPLATE

def clean_column_names(df):
    """Cleans dataframe column names."""
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')
    return df

def run_analysis_pipeline(df: pd.DataFrame, question: str, llm_option: str = "GPT-4o"):
    """
    Runs the full analysis pipeline for a given dataframe and question.
    This function is a non-Streamlit adaptation of the logic in app.py.
    """
    print("---" * 20)
    print(f"🚀 Starting Analysis for Question: {question}")
    print("---" * 20)

    try:
        llm = configure_llm(llm_option)
        
        # --- Step 1: Intent Detection ---
        print("\nStep 1: 识别用户意图...")
        intents = get_intents(question)
        print(f"🤖 已识别意图: {', '.join(intents)}")
        
        # --- Step 2: Simplify Query for Data Extraction ---
        print("\nStep 2: 简化用户问题用于数据提取...")
        simplification_prompt_str = SIMPLIFICATION_PROMPT_TEMPLATE.format(question=question)
        prompt_obj = BasePrompt()
        prompt_obj._resolved_prompt = simplification_prompt_str
        simplified_question = llm.call(prompt_obj)
        print("📝 简化后的提取问题:")
        print(simplified_question)

        # --- Step 3: PandasAI Agent for Data Extraction ---
        print("\nStep 3: 使用 PandasAI Agent 提取分析所需数据...")
        extraction_agent = create_extraction_agent(df, llm)
        extracted_data_response = chat_with_agent(extraction_agent, simplified_question)
        
        # --- Step 4: Response Handling ---
        print("\nStep 4: 处理响应并生成最终结果...")
        
        if isinstance(extracted_data_response, DataFrameResponse):
            extracted_df = extracted_data_response.value
            print("📊 提取的数据 (前5行):")
            print(extracted_df.head())
            
            if extracted_df.empty:
                print("⚠️ 数据提取步骤未能找到相关数据。")
                return

            if "string" in intents:
                print("\n  -> 'string' 意图检测到，开始文本分析...")
                # --- Step 4a: Generate Dynamic Analysis Guidance ---
                print("\n    Step 4a: 生成动态分析指导...")
                data_sample_csv = extracted_df.head().to_csv(index=False)
                prompt_for_guidance = GUIDANCE_PROMPT_TEMPLATE.format(
                    question=question,
                    data_sample=data_sample_csv
                )
                guidance_prompt_obj = BasePrompt()
                guidance_prompt_obj._resolved_prompt = prompt_for_guidance
                analysis_guidance = llm.call(guidance_prompt_obj)
                print("    📖 生成的分析指导:")
                print(analysis_guidance)

                # --- Step 4b: Generate Final Report using Guidance ---
                print("\n    Step 4b: 使用动态指导生成最终分析报告...")
                data_csv = extracted_df.to_csv(index=False)
                final_prompt_str = ANALYSIS_PROMPT_TEMPLATE.format(
                    query=question,
                    guidance=analysis_guidance,
                    data=data_csv
                )
                prompt_obj = BasePrompt()
                prompt_obj._resolved_prompt = final_prompt_str
                analysis_report = llm.call(prompt_obj)
                
                print("\n" + "---" * 10 + " FINAL REPORT " + "---" * 10)
                print(analysis_report)
                print("---" * 22)

        elif isinstance(extracted_data_response, ChartResponse):
            chart_path = extracted_data_response.value
            print(f"\n📈 图表已生成并保存于: {chart_path}")

        else:
            print(f"❌ 数据提取失败或返回了不支持的响应类型: {type(extracted_data_response)}")
            print(extracted_data_response)

    except Exception as e:
        print(f"💥 分析流程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run all test cases."""
    
    # --- Test cases for '变现群小机器人收入数据.csv' ---
    csv_path_1 = "data/变现群小机器人收入数据.csv"
    print(f"\n\n{'='*25}\n 运行文件: {csv_path_1} \n{'='*25}")
    try:
        df1 = pd.read_csv(csv_path_1)
        df1 = clean_column_names(df1)
        
        test_cases_1 = [
            "计算下 3到6月每个月的月均总收入",
            "请画出2025年3月到6月月均总收入的折线图",
            "分析下为什么20250601收入比20250501收入低？从多个角度分析 因为数据里有各个变现场景的数据"
        ]
        
        for i, case in enumerate(test_cases_1, 1):
            run_analysis_pipeline(df1, case)

    except FileNotFoundError:
        print(f"❌ 文件未找到: {csv_path_1}")
    except Exception as e:
        print(f"处理 {csv_path_1} 时发生错误: {e}")

    # --- Test cases for '充值数据.csv' ---
    csv_path_2 = "data/充值数据.csv"
    print(f"\n\n{'='*25}\n 运行文件: {csv_path_2} \n{'='*25}")
    try:
        df2 = pd.read_csv(csv_path_2)
        df2 = clean_column_names(df2)
        
        test_cases_2 = [
            "那2025年6月1日比5月1日收入下降，主要受到充值人数减少的影响还是受到充值arpu值的影响？如果充值人数减少的原因是什么，和DAU减少有关系吗？还是充值率降低了呢？同理，arpu值也是一样的推理，麻烦给我一个综合的分析判断。",
            "分析2025年1月至5月对比2024年的1月至5月，各字段按月求每个月的日平均值，根据每个月的日平均值同比2024年，给出分析结论",
            "哪天收入最高 收入是多少"
        ]

        for i, case in enumerate(test_cases_2, 1):
            run_analysis_pipeline(df2, case)
            
    except FileNotFoundError:
        print(f"❌ 文件未找到: {csv_path_2}")
    except Exception as e:
        print(f"处理 {csv_path_2} 时发生错误: {e}")


if __name__ == "__main__":
    main() 