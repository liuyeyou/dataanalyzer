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
"""

SIMPLIFICATION_PROMPT_TEMPLATE = """You are an expert at simplifying complex data analysis questions into a clear data extraction query. Your task is to read the user's potentially complex question and extract ONLY the core data requirements, such as specific dates, entities, or categories.

**User's Original Question:**
"{question}"

**Your Output:**
A single, direct question focused purely on data retrieval.

**Examples:**
- **Original:** "那2025年6月1日比5月1日收入下降，主要受到充值人数减少的影响还是受到充值arpu值的影响？如果充值人数减少的原因是什么，和DAU减少有关系吗？"
  **Your Simplified Output:** "请提取行为时间为'2025-05-01'和'2025-06-01'的所有数据。"
- **Original:** "分析一下3月份和4月份A产品的销售趋势和用户反馈"
  **Your Simplified Output:** "请提取3月份和4月份A产品的相关数据。"
- **Original:** "给我画一下过去三个月DAU的变化曲线"
  **Your Simplified Output:** "请提取过去三个月的DAU数据。"
"""