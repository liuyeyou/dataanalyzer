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
    
    api_url: Optional[str] = Field(default_factory=lambda: os.getenv("DEEPSEEK_API_URL"))
    api_headers: Dict[str, str] = Field(default={"Content-Type": "application/json"})
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def _generate(
        self, 
        messages: List[BaseMessage], 
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        if not self.api_url:
            raise ValueError("DEEPSEEEK_API_URL is not set for CustomDeepseekChat")

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
google_api_key = "AIzaSyDT2WMlb-t7ienDhaYv3RENEs7ML3UlfE0"

if not google_api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# 初始化 LLMs
llm_gemini = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0, google_api_key=google_api_key)

# 只有当 DEEPSEEK_API_URL 存在时才初始化 llm_deepseek
llm_deepseek = None
if os.getenv("DEEPSEEK_API_URL"):
    llm_deepseek = CustomDeepseekChat()

# 默认使用 Gemini
selected_llm = llm_gemini

def set_llm(llm_name):
    """设置要使用的 LLM"""
    global selected_llm
    if llm_name.lower() == "gemini":
        selected_llm = llm_gemini
    elif llm_name.lower() == "deepseek" and llm_deepseek:
        selected_llm = llm_deepseek
    else:
        raise ValueError(f"Unknown LLM or Deepseek API URL not configured: {llm_name}")

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
    df = get_dataframe(filename)
    
    pandas_agent = create_pandas_dataframe_agent(
        llm=selected_llm,
        df=df,
        verbose=True,
        allow_dangerous_code=True,
        agent_executor_kwargs={"handle_parsing_errors": "True"},
    )

    response = pandas_agent.run(f"请用中文分析 \"{variable}\" 的趋势")
    return response

def ask_question(filename, question):
    df = get_dataframe(filename)
    
    pandas_agent = create_pandas_dataframe_agent(
        llm=selected_llm,
        df=df,
        verbose=True,
        allow_dangerous_code=True,
        agent_executor_kwargs={"handle_parsing_errors": "True"},
    )

    base_prompt = f"""
    请分析以下问题: "{question}"

    要求：
    1. 如果问题涉及数值分析：
       - 提供具体的数据支持
       - 计算相关的统计指标
       - 说明数据的变化情况

    2. 如果问题涉及趋势分析：
       - 分析整体趋势
       - 找出关键的变化点
       - 解释可能的原因

    3. 如果问题涉及比较：
       - 详细列出比较项的具体数据
       - 分析差异和变化
       - 探讨变化的原因

    4. 补充分析：
       - 如果发现异常或特殊情况，请说明
       - 如果有相关的业务建议，请提出
       - 如果需要更多上下文信息，请说明

    请用中文回答，注意：
    - 保持专业性和准确性
    - 数据分析要有逻辑性
    - 结论要有数据支持
    """
    
    AI_response = pandas_agent.run(base_prompt)
    return AI_response
