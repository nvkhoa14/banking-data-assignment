import streamlit as st
import os
import pandas as pd
import altair as alt
from sqlalchemy import create_engine, text

# Connect to the database
DATABASE_URL = os.environ['DATABASE_URL']
engine = create_engine(DATABASE_URL)

@st.cache_data(ttl=30)
def query(sql: str) -> pd.DataFrame:
    return pd.read_sql_query(text(sql), engine)

st.title("Banking Dashboard")

st.header("Risky Transactions")
risky_transactions_sql = """
                        SELECT tag_reason, severity, count(*) total_failures
                        FROM banking.risk_tag rt
                        GROUP BY rt.tag_reason, rt.severity
                        ORDER BY total_failures DESC;
                        """
risky_transactions_df = query(risky_transactions_sql)
st.table(risky_transactions_df)

st.header("Top 5 Customers with Most Failures")
failure_sql = """
                    -- 1) Aggregate & rank failures by auth_type
                    WITH failure_auth_counts as (
                        SELECT auth.auth_type, acc.customer_id, count(*) total_failures
                        FROM banking.transaction tx
                        JOIN banking.account acc ON tx.account_id = acc.account_id
                        JOIN banking.auth_log auth ON tx.tx_id = auth.tx_id
                        WHERE tx.status = 'failed'
                        GROUP BY auth.auth_type, acc.customer_id
                    ),
                    ranked_failures AS (
                    SELECT
                        auth_type as fail_type, customer_id, total_failures,
                        ROW_NUMBER() OVER (PARTITION BY auth_type ORDER BY total_failures DESC) AS rn
                    FROM failure_auth_counts
                    ),

                    -- 2) Select top 5 failures for untrusted devices
                    untrusted_failures AS (
                        SELECT acc.customer_id, count(*) total_failures
                        FROM banking.risk_tag rt
                        JOIN banking.transaction tx on rt.tx_id = tx.tx_id
                        JOIN banking.account acc on tx.account_id = acc.account_id
                        WHERE rt.severity = 4
                        GROUP BY acc.customer_id
                    ),
                    ranked_unstrusted AS (
                        SELECT 'UNTRUSTED DEVICES' AS fail_type, customer_id, total_failures,
                        ROW_NUMBER() OVER (ORDER BY total_failures DESC) AS rn
                    FROM untrusted_failures
                    )

                    -- 3) Combine results and select top 5 for each auth_type
                    SELECT fail_type, customer_id, total_failures
                    FROM ranked_failures
                    WHERE rn <= 5

                    UNION ALL

                    SELECT fail_type, customer_id, total_failures
                    FROM ranked_unstrusted
                    WHERE rn <= 5
                    ORDER BY fail_type, total_failures DESC;
                    """
failure_df = query(failure_sql)
st.table(failure_df)

# Visualize the top 5 customers with most failures
base = (
    alt.Chart(failure_df)
       .mark_bar()
       .encode(
           x=alt.X("total_failures:Q", title="Failures"),
           y=alt.Y("customer_id:N", sort="-x", title="Customer"),
           color=alt.Color("fail_type:N", legend=None)
       )
       .properties(
           width=400,   
           height=400
       )    
)
st.altair_chart(base, use_container_width=True)


                        

