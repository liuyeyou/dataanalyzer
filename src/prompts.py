ANALYSIS_PROMPT_TEMPLATE = """You are a world-class data analyst. I will provide you with data in CSV format and a user's question. Your task is to perform a detailed analysis and generate a comprehensive, structured analysis report in Markdown format.

**User's Question:**
{query}

**Data (in CSV format):**
```csv
{data}
```

**YOUR TASK:**
Based *only* on the data provided, answer the user's question. Your response MUST be a single, formatted Markdown string that follows this structure:

**General Markdown Template:**
```markdown
📊 【分析摘要】
- 分析主题: [Summarize the user's request, e.g., '2025-06-01 与 2025-05-01 的总收入对比分析']
- 核心指标: [Identify the key metric from the query, e.g., '总收入']

📉 【核心指标对比】
- [Metric Name] 对比: [Entity A]'s value was [Value A], and [Entity B]'s value was [Value B].
- 变化情况: The metric [increased/decreased] by [Absolute Difference], a change of [Percentage Change].

🔎 【深入原因探查】
- 主要驱动因素: [Analyze the sub-components to find the main driver of the change. E.g., "The decrease was primarily driven by 'Web充值收入', which fell from X to Y."]
- 其他相关观察: [Provide any other relevant insights from the data.]
```
""" 