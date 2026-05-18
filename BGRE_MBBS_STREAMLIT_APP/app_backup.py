import streamlit as st
import pandas as pd
import snowflake.connector

st.title("BGRE Live Dashboard")

conn = snowflake.connector.connect(
    user="BGRE_CLIENT",
    password="BGRE@123456789a",
    account="TVSNEXT-TVSNEXT",
    warehouse="BGRE_WH",
    database="SNOWFLAKE_POC",
    schema="ME2J_SCHEMA"
)

query = """
SELECT *
FROM ME2J_FINAL_REPORT
LIMIT 100
"""

df = pd.read_sql(query, conn)

st.subheader("ME2J Final Report")
st.dataframe(df)