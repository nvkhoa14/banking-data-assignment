"""
data_quality_standards.py

Performs schema‐level and value‐level data quality checks on the banking schema.
"""

import os
import re
import sys
import logging
import psycopg2

DB_HOST     = os.getenv("POSTGRES_HOST", "")
DB_PORT     = os.getenv("POSTGRES_PORT", 5432)
DB_NAME     = os.getenv("POSTGRES_DB", "banking")
DB_USER     = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secret")

HIGH_VALUE_THRESHOLD = 10_000_000  # VND

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()]
)

def connect_db():
    return psycopg2.connect(
        host=DB_HOST or None,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# Null / Missing Checks
def check_not_null(table, column):
    sql = f"""
      SELECT COUNT(*) 
      FROM {table} 
      WHERE {column} IS NULL;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        cnt = cur.fetchone()[0]
        if cnt:
            logging.error(f"{cnt} NULL(s) found in {table}.{column}")
        else:
            logging.info(f"OK: no NULLs in {table}.{column}")

# Uniqueness Checks
def check_unique(table, column):
    sql = f"""
      SELECT {column}, COUNT(*) 
      FROM {table} 
      GROUP BY {column}
      HAVING COUNT(*) > 1;
    """
    cur.execute(sql)
    if cur.rowcount > 0:
        logging.error(f"Duplicates in {table}.{column}: {rows[:5]}{'…' if len(rows)>5 else ''}")
    else:
        logging.info(f"OK: all values unique in {table}.{column}")

# Format / Length Checks (CCCD = 12 digits)
def check_cccd_format():
    sql = f"""
      SELECT customer_id, id_number
      FROM customer;
    """
    bad = []
    pattern = re.compile(r"^\d{12}$")
    cur.execute(sql)
    for cust_id, id_number in cur.fetchall():
        if not pattern.match(id_number or ""):
            bad.append((cust_id, id_number))
    if bad:
        logging.error(f"Found {len(bad)} invalid CCCDs: {bad[:3]}{'…' if len(bad)>3 else ''}")
    else:
        logging.info("OK: all CCCDs match \\d{12}")

# Foreign Key Integrity
def check_fk(child_table, child_col, parent_table, parent_col):
    sql = f"""
      SELECT COUNT(*) 
      FROM {child_table} c
      LEFT JOIN {parent_table} p
        ON c.{child_col} = p.{parent_col}
      WHERE p.{parent_col} IS NULL;
    """
    cur.execute(sql)
    if cur.rowcount == 0:
        logging.error(f"{cnt} orphan rows in {child_table}.{child_col} → no match in {parent_table}.{parent_col}")
    else:
        logging.info(f"OK: all {child_table}.{child_col} have valid parent in {parent_table}")

if __name__ == "__main__":
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SET search_path TO banking;") 
    try:
        # 1. Not-null on critical columns
        check_not_null("customer", "customer_id")
        check_not_null("customer", "id_number")
        check_not_null("account",  "account_id")
        check_not_null("transaction", "tx_id")
        check_not_null("auth_log", "auth_id")

        # 2. Uniqueness
        check_unique("customer", "contact")     # phone/email unique
        check_unique("customer", "customer_id")
        check_unique("account",  "account_id")
        check_unique("transaction", "tx_id")

        # 3. Format
        check_cccd_format()

        # 4. Foreign keys
        check_fk("account", "customer_id",   "customer",    "customer_id")
        check_fk("transaction", "account_id", "account",    "account_id")
        check_fk("auth_log", "tx_id",         "transaction", "tx_id")
        check_fk("device", "customer_id",     "customer",    "customer_id")
        check_fk("risk_tag", "tx_id",         "transaction", "tx_id")

    finally:
        conn.close()
