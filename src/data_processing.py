import pandas as pd
import re
import streamlit as st

def load_and_process_data(uploaded_file, container):
    """
    Reads an uploaded CSV file, handles different encodings, 
    cleans column names, and displays a sample of the data.
    Returns a processed pandas DataFrame.
    """
    if not uploaded_file:
        return None

    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(uploaded_file, encoding='gbk')
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding='latin1')
            
    # Clean column names
    new_columns = {col: re.sub(r'[^\w\u4e00-\u9fa5]', '', str(col)) for col in df.columns}
    df.rename(columns=new_columns, inplace=True)
    
    with container:
        st.success(f'数据文件 "{uploaded_file.name}" 加载成功。')
        st.write("数据样本:", df.head())
        st.divider()
    
    return df 