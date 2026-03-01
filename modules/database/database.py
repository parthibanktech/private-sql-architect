import sqlite3
import pandas as pd
import os

def execute_sql(query):
    db_path = "data/databases/demo.db"
    
    # Ensure directory exists just in case
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)
