"""
Simulates random banking transactions—deposits, withdrawals, and transfers—
while enforcing ACID, strong‐auth rules, balance checks, and risk tagging.
"""

import os
import uuid
import random
import logging
from datetime import datetime
import psycopg2
from psycopg2 import sql

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

# Check if a device is trusted for a given account
def check_device_trust(cur, account_id, device_id):
    cur.execute("""
                SELECT ac.account_id, d.device_id 
                FROM banking.account ac
                JOIN banking.device d ON d.customer_id = ac.customer_id
                WHERE d.device_id = %s AND ac.account_id = %s;
            """, (device_id, account_id))

# Update the balance of an account in the database.
def update_account_balance(cur, account_id, amount):
    # Update the balance of an account in the database.
    cur.execute("""
        UPDATE banking.account
        SET balance = balance + %s
        WHERE account_id = %s AND balance + %s >= 0;
    """, (amount, account_id, amount))

# Update the status of a transaction in the database.
def update_transaction_status(cur, tx_id, status):
    # Update the status of a transaction in the database.
    cur.execute("""
        UPDATE banking.transaction
        SET status = %s
        WHERE tx_id = %s;
    """, (status, tx_id))

# Generate a risk tag for a transaction.
def generate_risk(cur, tx_id, severity=1, tag_reason=''):
    # Generate a risk ID for a transaction.
    risk_id = str(uuid.uuid4())
    cur.execute("""
            INSERT INTO banking.risk_tag (risk_id, tx_id, severity, tag_reason)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (risk_id) DO NOTHING;
        """, (risk_id, tx_id, severity, tag_reason))

# Define the authentication type based on transaction amount.
def define_high_value_transaction(cur, tx_id, amount):
    # Tag high-value transactions for additional scrutiny.
    # This function inserts a risk tag into the database if the amount exceeds the threshold.
    
    if amount > HIGH_VALUE_THRESHOLD:
        generate_risk(cur, tx_id, 2, 'High value transaction')
        logging.warning(f"Transaction {tx_id} tagged as high value due to amount {amount}.")
        return random.choice(['Biometric', 'OTP'])      # Strong authentication required for high-value transactions
    
    cur.execute("""
            WITH cte AS (
                SELECT c.customer_id cus, tx.tx_id tx_id, tx.amount amt, DATE(tx.timestamp) time
                FROM banking.customer c
                JOIN banking.account acc ON c.customer_id = acc.customer_id 
                JOIN banking.transaction tx ON acc.account_id = tx.account_id 
                WHERE DATE(tx.timestamp) = DATE(NOW()) 
            )
            SELECT cus, sum(abs(amt))
            FROM cte
            WHERE cus = (SELECT cus FROM cte WHERE tx_id = %s) 
            GROUP BY cus, time
            HAVING sum(abs(amt)) > 20000000;
        """, (tx_id,))
    
    if cur.rowcount > 0:
        generate_risk(cur, tx_id, 3, 'Cumulative amount exceeds 20,000,000 VND')
        logging.warning(f"Transaction {tx_id} tagged as high value due to cumulative amount exceeding 20,000,000 VND.")
        return 'Biometric'      # Strong authentication required for high-value transactions

    return 'PIN'            # Default authentication for regular transactions

# Process a transaction based on its type and perform necessary checks.
def process_transaction(conn, cur, tx):
    tx_id, account_id, device_id, target_id, amount = tx
    
    if target_id:           # Transfer
        # Check if the device is trusted for the account
        check_device_trust(cur, account_id, device_id)
        if cur.rowcount == 0:
            update_transaction_status(cur, tx_id, 'failed')
            generate_risk(cur, tx_id, 4, 'Untrusted device')
            raise ValueError(f"Device {device_id} is not trusted.")
        
        # Begin transaction
        update_account_balance(cur, account_id, -amount)    # Deduct from source account
        if cur.rowcount == 0:
            update_transaction_status(cur, tx_id, 'failed')
            raise ValueError(f"Transfer Fail (insufficient balance)")
        
        # Simulate strong authentication failure or success
        status = random.choice(['success', 'failed'])

        # Create a transaction_auth record
        auth_id = str(uuid.uuid4())
        auth_type = define_high_value_transaction(cur, tx_id, amount)
        cur.execute("""
            INSERT INTO banking.auth_log (auth_id, tx_id, auth_type)
            VALUES (%s, %s, %s)
            ON CONFLICT (auth_id) DO NOTHING;
        """, (auth_id, tx_id, auth_type))

        # Update transaction status based on authentication
        if status == 'failed':
            conn.rollback()                 # Rollback if authentication fails
            update_transaction_status(cur, tx_id, 'failed')
            cur.execute("""
                UPDATE banking.auth_log
                SET success_flag = FALSE
                WHERE auth_id = %s;
            """, (auth_id,))

            raise ValueError(f"Authentication Failed")
        else:
            cur.execute("""
                UPDATE banking.auth_log
                SET success_flag = TRUE
                WHERE auth_id = %s;
            """, (auth_id,))
            update_account_balance(cur, target_id, amount) 
            logging.info(f"Transaction {tx_id}: Transfer Success")
            
    else:                           # No authentication needed for deposit/withdrawal
        if amount < 0:              # Withdrawal
            update_account_balance(cur, account_id, amount) 
            if cur.rowcount == 0:   # Insufficient balance
                update_transaction_status(cur, tx_id, 'failed')
                raise ValueError(f"Withdrawal Fail (insufficient balance)")
        else:                       # Deposit 
            update_account_balance(cur, account_id, amount)
            logging.info(f"Transaction {tx_id}: Deposit Success")
    
    # Transaction completed successfully, update status
    update_transaction_status(cur, tx_id, 'success')
    
if __name__ == "__main__":
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT tx_id, account_id, device_id, target_id, amount
            FROM banking.transaction
            WHERE status = 'pending';
        """)
        rows = cur.fetchall()
        if not rows:
            logging.info("No pending transactions to process.")
        else:
            for tx in rows:
                try:
                    process_transaction(conn, cur, tx)
                except Exception as e:
                    logging.error(f"Transaction {tx[0]} : {e}")
                conn.commit()
            cur.close()
            print("All pending transactions processed successfully.")