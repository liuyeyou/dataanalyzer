import pandasai as pai
import os

def create_extraction_agent(df, llm):
    """
    Creates a specialized agent for broad data extraction, intended for deep analysis.
    Uses SQL for querying.
    """
    pai_df = pai.DataFrame(df)
    
    save_path = os.path.join(os.getcwd(), "exports/charts")
    os.makedirs(save_path, exist_ok=True)

    # This prompt is critical for deep analysis. It instructs the LLM to fetch
    # all columns to enable a comprehensive root cause analysis, even if the
    # user's simplified query only mentions a single metric.
    system_prompt = """
Your sole job is to act as a data extraction engine for a root cause analysis.
Based on the user's question, your primary task is to generate a SQL query
that fetches ALL columns that could be relevant from the table. Do not
limit the selection to just the specific metric mentioned in the query. For example,
if the user asks about a change in 'revenue', you must also fetch user data,
regional data, and other metrics, because the reason for the change is likely
found in those other columns.

Return only the resulting dataframe. Select all available columns for the rows matching the user's date criteria.
"""

    config = {
        "llm": llm,
        "verbose": True,
        "enable_cache": False,
        "use_sql": True,
        "custom_whitelisted_dependencies": ["pandas"],
        "system_prompt": system_prompt,
        "save_charts_path": save_path,
    }
    
    return pai.Agent([pai_df], config=config)

def create_processing_agent(df, llm):
    """
    Creates a general-purpose agent capable of generating charts,
    performing calculations, and returning dataframes or strings.
    Uses Python execution.
    """
    pai_df = pai.DataFrame(df)
    
    save_path = os.path.join(os.getcwd(), "exports/charts")
    os.makedirs(save_path, exist_ok=True)

    config = {
        "llm": llm,
        "verbose": True,
        "enable_cache": False,
        "use_sql": False, # Use python code for plotting and calculations
        "save_charts": True,
        "save_charts_path": save_path,
    }
    
    return pai.Agent([pai_df], config=config)

def chat_with_agent(agent, question: str):
    """
    Sends a question to the agent and returns the response.
    """
    return agent.chat(question)