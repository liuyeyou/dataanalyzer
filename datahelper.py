import os
import json
import requests
import pandas as pd
from typing import Any, List, Optional, Dict
from dotenv import load_dotenv
from langchain_experimental.agents.agent_toolkits.pandas.base import (
    create_pandas_dataframe_agent,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chat_models.base import BaseChatModel
from langchain.schema import HumanMessage, AIMessage, SystemMessage, BaseMessage, ChatResult, ChatGeneration
from pydantic import Field, ConfigDict

class CustomDeepseekChat(BaseChatModel):
    """自定义 Deepseek Chat 模型"""
    
    api_url: str = Field(default="http://119.63.197.152:8903/v1/chat/completions")
    api_headers: Dict[str, str] = Field(default={"Content-Type": "application/json"})
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def _generate(
        self, 
        messages: List[BaseMessage], 
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # 添加系统提示要求输出中文
        system_message = {"role": "system", "content": "请用中文回答所有问题，保持专业性和准确性。"}
        formatted_messages = [system_message]
        
        for message in messages:
            if isinstance(message, HumanMessage):
                formatted_messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                formatted_messages.append({"role": "assistant", "content": message.content})
            elif isinstance(message, SystemMessage):
                formatted_messages.append({"role": "system", "content": message.content})
        
        data = {
            "model": "/root/deepseek/",
            "messages": formatted_messages,
            "temperature": 0.3,
            "max_tokens": 4000,
            "stream": False
        }
        
        response = requests.post(self.api_url, headers=self.api_headers, json=data)
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            message = AIMessage(content=content)
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])
        else:
            raise Exception(f"API call failed with status code: {response.status_code}")
    
    @property
    def _llm_type(self):
        return "custom_deepseek"

load_dotenv()

# 初始化 API 密钥
google_api_key = os.getenv("GOOGLE_API_KEY")

if not google_api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# 初始化 LLMs
llm_gemini = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0, google_api_key=google_api_key)
llm_deepseek = CustomDeepseekChat()

# 默认使用 Gemini
selected_llm = llm_gemini

def set_llm(llm_name):
    """设置要使用的 LLM"""
    global selected_llm
    if llm_name.lower() == "gemini":
        selected_llm = llm_gemini
    elif llm_name.lower() == "deepseek":
        selected_llm = llm_deepseek
    else:
        raise ValueError(f"Unknown LLM: {llm_name}")

def detect_file_encoding(filename):
    """
    检测文件编码并返回编码类型
    """
    encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'utf-16']
    for encoding in encodings:
        try:
            with open(filename, 'r', encoding=encoding) as f:
                f.read()
                return encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"无法检测文件编码，尝试过的编码：{encodings}")

def get_date_column(df):
    """
    智能检测日期列
    """
    # 常见的日期列名
    date_column_names = ['日期', 'date', 'time', 'datetime', '时间', '日', '年月日','行为时间']
    
    # 检查是否存在这些列名
    for col in date_column_names:
        if col in df.columns:
            return col
            
    # 如果没有找到常见的日期列名，尝试通过数据类型推断
    for col in df.columns:
        # 尝试将列转换为日期格式
        try:
            pd.to_datetime(df[col])
            return col
        except:
            continue
            
    # 如果还是没找到，打印所有列名并抛出异常
    raise ValueError(f"无法找到日期列。当前文件包含以下列：{', '.join(df.columns)}")

def read_csv_with_encoding(filename, **kwargs):
    """
    智能读取 CSV 文件，自动处理编码问题
    """
    try:
        # 首先尝试检测编码
        encoding = detect_file_encoding(filename)
        df = pd.read_csv(filename, encoding=encoding, **kwargs)
        # 打印列名，帮助调试
        print(f"成功读取文件，包含以下列：{', '.join(df.columns)}")
        return df
    except Exception as e:
        # 如果检测失败，尝试常用编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'utf-16']
        for encoding in encodings:
            try:
                df = pd.read_csv(filename, encoding=encoding, **kwargs)
                print(f"成功读取文件（使用 {encoding} 编码），包含以下列：{', '.join(df.columns)}")
                return df
            except UnicodeDecodeError:
                continue
        # 如果所有编码都失败，抛出异常
        raise UnicodeDecodeError(f"无法读取文件，尝试过的编码：{encodings}")

def summerize_csv(filename):
    df = read_csv_with_encoding(filename, low_memory=False)
    
    try:
        # 智能检测日期列
        date_column = get_date_column(df)
        print(f"使用 '{date_column}' 作为日期列")
        
        # 将日期列转换为datetime，只保留年月日
        df[date_column] = pd.to_datetime(df[date_column]).dt.date
        
        # 如果列名不是'日期'，重命名为'日期'以保持一致性
        if date_column != '日期':
            df = df.rename(columns={date_column: '日期'})
    except Exception as e:
        print(f"处理日期列时出错：{str(e)}")
        raise

    pandas_agent = create_pandas_dataframe_agent(
        llm=selected_llm,
        df=df,
        verbose=True,
        allow_dangerous_code=True,
        agent_executor_kwargs={"handle_parsing_errors": "True"},
    )

    data_summary = {}

    data_summary["initial_data_sample"] = df.head()

    data_summary["column_descriptions"] = pandas_agent.run(
        f"请用中文创建一个数据集列的表格。包含列名和列的描述。"
    )

    data_summary["missing_values"] = pandas_agent.run(
        "请用中文回答：数据集中是否有缺失值？如果有，有多少个？回答格式应该是'该数据集中有X个缺失值'"
    )

    data_summary["dupplicate_values"] = pandas_agent.run(
        "请用中文回答：数据集中是否有重复值？如果有，有多少个？回答格式应该是'该数据集中有X个重复值'"
    )

    data_summary["essential_metrics"] = df.describe()

    return data_summary

def get_dataframe(filename):
    df = read_csv_with_encoding(filename, low_memory=False)
    
    try:
        # 智能检测日期列
        date_column = get_date_column(df)
        print(f"使用 '{date_column}' 作为日期列")
        
        # 将日期列转换为datetime，只保留年月日
        df[date_column] = pd.to_datetime(df[date_column]).dt.date
        
        # 如果列名不是'日期'，重命名为'日期'以保持一致性
        if date_column != '日期':
            df = df.rename(columns={date_column: '日期'})
    except Exception as e:
        print(f"处理日期列时出错：{str(e)}")
        raise
    
    return df

def analyze_trend(filename, variable):
    df = read_csv_with_encoding(filename, low_memory=False)
    
    try:
        # 智能检测日期列
        date_column = get_date_column(df)
        print(f"使用 '{date_column}' 作为日期列")
        
        # 将日期列转换为datetime，只保留年月日
        df[date_column] = pd.to_datetime(df[date_column]).dt.date
        
        # 如果列名不是'日期'，重命名为'日期'以保持一致性
        if date_column != '日期':
            df = df.rename(columns={date_column: '日期'})
    except Exception as e:
        print(f"处理日期列时出错：{str(e)}")
        raise

    pandas_agent = create_pandas_dataframe_agent(
        llm=selected_llm,
        df=df,
        verbose=True,
        agent_executor_kwargs={"handle_parsing_errors": "True"},
        allow_dangerous_code=True,
    )

    trend_response = pandas_agent.run(
        f"请简要解释这个变量的趋势：{variable}。请用中文回答。数据集的行是按时间顺序排列的，所以你可以通过查看数据集的行来解释趋势。"
    )

    return trend_response

def ask_question(filename, question):
    df = read_csv_with_encoding(filename, low_memory=False)
    
    try:
        # 智能检测日期列
        date_column = get_date_column(df)
        print(f"使用 '{date_column}' 作为日期列")
        
        # 将日期列转换为datetime，只保留年月日
        df[date_column] = pd.to_datetime(df[date_column]).dt.date
        
        # 如果列名不是'日期'，重命名为'日期'以保持一致性
        if date_column != '日期':
            df = df.rename(columns={date_column: '日期'})
    except Exception as e:
        print(f"处理日期列时出错：{str(e)}")
        raise

    pandas_agent = create_pandas_dataframe_agent(
        llm=selected_llm,
        df=df,
        verbose=True,
        agent_executor_kwargs={"handle_parsing_errors": "True"},
        allow_dangerous_code=True,
    )

    # 检查是否是日期收入比较问题
    if "收入" in question and any(date in question for date in ["2025", "月", "日"]):
        enhanced_prompt = f"""
        请对 {question} 进行详细分析，要求：
        
        1. 基础数据对比：
           - 两个日期的具体收入数据
           - 计算具体的变化金额和百分比
        
        2. 收入构成分析：
           - 分解各个收入来源（如web端、金币等）的具体数据
           - 计算每个收入来源的变化幅度
           - 找出变化最大的收入来源
        
        3. 变化原因分析：
           - 对比各收入来源的具体变化情况
           - 分析每个收入来源变化的可能原因
           - 重点解释变化最显著的部分
        
        4. 相关指标分析：
           - 分析相关的业务指标（如有）
           - 探讨指标变化与收入变化的关系
        
        5. 建议和预测：
           - 基于数据给出具体的改进建议
           - 如果看到任何异常趋势，请特别指出
        
        请用中文回答，确保：
        - 提供具体的数字和百分比
        - 分点列出各项分析结果
        - 重点标出异常或显著的变化
        """
        AI_response = pandas_agent.run(enhanced_prompt)
    else:
        # 对于其他类型的问题，添加基础提示
        base_prompt = f"""
        请对问题 "{question}" 进行分析，要求：
        1. 提供具体的数据支持
        2. 解释数据背后的含义
        3. 如果发现异常或特殊情况，请特别说明
        4. 如果可能，提供相关的建议
        
        请用中文回答，保持专业性和准确性。
        """
        AI_response = pandas_agent.run(base_prompt)

    return AI_response
