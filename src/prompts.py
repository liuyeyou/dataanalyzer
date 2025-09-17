ANALYSIS_PROMPT_TEMPLATE = """You are a world-class data analyst. I will provide you with data in CSV format, a user's question, and specific analysis guidance. Your task is to perform a detailed analysis and generate a comprehensive, structured analysis report in Markdown format.

**User's Question:**
{query}

**Specific Analysis Guidance:**
{guidance}

**Data (in CSV format):**
```csv
{data}
```

**YOUR TASK:**
Following the analysis guidance, and based *only* on the data provided, answer the user's question. Your response MUST be a single, formatted Markdown string. The structure of your response should be logical and clear, tailored to the user's question. Use the following general template as a guideline, but adapt it as needed.

**General Markdown Template Guideline:**
```markdown
📊 分析摘要 (Analysis Summary)**
- **分析目标 (Analysis Goal):** [Concisely restate the user's objective based on their question.]
- **核心发现 (Key Findings):** [Summarize the main conclusions from your analysis in 1-2 sentences.]

💡 **核心洞察 (Key Insights)**
- [Present the most important insight as a clear statement. Use tables, lists, or bold text to highlight key numbers and findings. The structure here should adapt to the query, for example, showing a comparison, a trend, or a distribution.]
- [Present another significant insight. This could be a deeper dive into the first insight or a separate observation.]
- [Continue with other relevant insights as necessary.]

⚙️ **详细分析 (Detailed Analysis)**
- [Provide the detailed data, calculations, or methodology that supports your key insights. This section justifies your findings from the section above.]
- [If necessary, include another section for further details to ensure clarity and completeness.]

📈 **后续建议 (Actionable Recommendations)**
- [Based on the insights, provide concrete and actionable recommendations.]
- [If applicable, suggest further analysis that could be performed for deeper understanding.]
```
"""

GUIDANCE_PROMPT_TEMPLATE = """You are a data analysis planner. Based on the user's question and a data sample, your task is to generate a concise, one-paragraph set of instructions for a data analyst LLM. These instructions should guide the analyst on exactly what to look for in the data. The guidance should be a logical, step-by-step plan.

**User's Question:**
"{question}"

**Data Sample (CSV format):**
```csv
{data_sample}
```

**Your Output:**
A single paragraph providing a logical, step-by-step analysis plan. For example: "To analyze user engagement, first calculate the overall trend of 'daily active users'. Next, segment these users by 'registration_source' to identify which sources contribute the most. Finally, examine the correlation between 'user_activity_level' and 'feature_adoption_rate' to uncover patterns in behavior."
请用中文回答
"""

SIMPLIFICATION_PROMPT_TEMPLATE = """You are an expert at simplifying complex data analysis questions into a clear data extraction query for a later analysis step. Your task is to read the user's potentially complex question and rephrase it into a direct command that asks for ALL relevant data connected to the core entities (like dates, products, or categories) mentioned. The goal is to gather comprehensive data, not just the specific metric in the question.

**User's Original Question:**
"{question}"

**Your Output:**
A single, direct question focused on retrieving all-encompassing data for the identified entities.

**Examples:**
- **Original:** "那2025年6月1日比5月1日收入下降，主要受到充值人数减少的影响还是受到充值arpu值的影响？如果充值人数减少的原因是什么，和DAU减少有关系吗？"
  **Your Simplified Output:** "请提取'2025-05-01'和'2025-06-01'这两天的所有列的数据。"
- **Original:** "分析一下3月份和4月份A产品的销售趋势和用户反馈"
  **Your Simplified Output:** "请提取3月份和4月份A产品的所有相关数据。"
- **Original:** "给我画一下过去三个月DAU的变化曲线，并分析一下原因"
  **Your Simplified Output:** "请提取过去三个月的所有相关数据。"
"""

PLOT_REQUEST_EXTRACTION_PROMPT_TEMPLATE = """From the user's query below, extract only the specific instruction for creating a plot. The output should be a concise, direct command for a plotting agent. Your response should contain only the plotting instruction and nothing else.

**User's Original Question:**
"{question}"

**Your Output:**
A single, direct question focused purely on plotting.

**Examples:**
- **Original:** "请画出2025年3月到6月月均总收入的折线图。 并分析下为什么20250601收入比20250501收入低？"
  **Your Simplified Output:** "画出2025年3月到6月月均总收入的折线图"
- **Original:** "分析一下3月份和4月份A产品的销售趋势和用户反馈, and also plot the sales trend"
  **Your Simplified Output:** "Plot the sales trend for product A in March and April."
- **Original:** "给我过去三个月DAU的变化曲线"
  **Your Simplified Output:** "画出过去三个月的DAU变化曲线"
"""

DATAFRAME_REQUEST_EXTRACTION_PROMPT_TEMPLATE = """From the user's query below, extract only the specific instruction for creating or calculating a table of data. Do not include any instructions for plotting. If the query is only about plotting, return an empty string.

**User's Original Question:**
"{question}"

**Your Output:**
A single, direct question focused purely on data calculation and retrieval.

**Examples:**
- **Original:** "计算下 3到6月每个月的月均总收入 给出表格并画出折线图"
  **Your Simplified Output:** "计算下 3到6月每个月的月均总收入并给出表格"
- **Original:** "画出过去三个月的DAU变化曲线"
  **Your Simplified Output:** ""
- **Original:** "What is the total revenue?"
  **Your Simplified Output:** "What is the total revenue?"
"""

ANALYSIS_TYPE_PROMPT_TEMPLATE = """You are an expert at classifying user questions about data. Classify the user's question into one of two categories: 'simple_lookup' or 'deep_analysis'.

- 'simple_lookup': The user is asking for a specific data point, a simple calculation, or a direct retrieval. Examples: "What was the total revenue on May 1st?", "Which day had the highest income?", "List all transactions for user X."
- 'deep_analysis': The user is asking for reasons, causes, comparisons, trends, or a comprehensive explanation. Examples: "Why did revenue drop in June compared to May?", "Analyze the sales trend for the last quarter.", "What are the key factors influencing user churn?"

Based on the definition, classify the following question. Respond with only 'simple_lookup' or 'deep_analysis'.

**User's Original Question:**
"{question}"

**Your Output:**
"""

SIMPLE_ANSWER_PROMPT_TEMPLATE = """You are a helpful data assistant. Based on the user's question and the provided data, give a direct and concise answer. Do not generate a full report, just provide the specific information requested.

**User's Question:**
{query}

**Data (in CSV format):**
```csv
{data}
```

**Your Answer:**
"""

INTENT_DETECTION_PROMPT_TEMPLATE = """You are an intent recognition assistant. Please determine the user's intent based on their question, there can be multiple intents (separated by English commas, in the order of plot, dataframe, string).

The intent definitions are as follows:
- plot: The user wants to generate a chart (e.g., bar chart, line chart, pie chart)
- dataframe: The user wants to get a table, column, or detailed data
- string: The user wants to get a text summary, explanation, or brief analysis

Please determine the intent of the following question, no explanation needed, just output the intent keywords:
Question: {query}
"""
