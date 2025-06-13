import pandasai as pai
import os

def create_extraction_agent(df, llm):
    """
    Creates a specialized agent whose ONLY job is to extract a comprehensive
    dataframe based on the user's query.
    """
    pai_df = pai.DataFrame(df)
    
    save_path = os.path.join(os.getcwd(), "exports/charts")
    os.makedirs(save_path, exist_ok=True)

    # A minimal, clear prompt for data extraction.
    # We are asking it to infer the necessary columns for a comprehensive analysis.
    system_prompt = """
Your sole job is to act as a data extraction engine. Based on the user's question,
your task is to generate a Python script that calls `execute_sql_query` to fetch ALL
potentially relevant columns from the table to answer the question. For example, if asked
about revenue changes, you must fetch not just the total revenue, but also all its
sub-components to enable a root cause analysis. Return only the resulting dataframe.
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

def chat_with_agent(agent, question: str):
    """
    Sends a question to the agent and returns the response.
    """
    # The question to the extraction agent should be a clear instruction.
    extraction_question = f"For the user's question '{question}', please extract all relevant data columns for a detailed analysis."
    return agent.chat(extraction_question)