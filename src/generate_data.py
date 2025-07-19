import uuid, random
from datetime import datetime, timedelta
from faker import Faker
import os
import psycopg2

# read database connection info from environment
DB_HOST     = os.getenv("POSTGRES_HOST", "")
DB_PORT     = os.getenv("POSTGRES_PORT", 5432)
DB_NAME     = os.getenv("POSTGRES_DB", "banking")
DB_USER     = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secret")

# open a connection to the database
def connect_db():
    return psycopg2.connect(
        host=DB_HOST or None,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# initialize Faker for Vietnam locale
fake = Faker("vi_VN")

# generate random data for customers
def generate_customer(cur, n = 1000):
    for _ in range(n):
        customer_id = str(uuid.uuid4())
        full_name = fake.name()
        birth_date = fake.date_of_birth(minimum_age=18, maximum_age=80)
        id_number = fake.numerify("############")      # VN ID number format
        contact = fake.phone_number()
        cur.execute(
            """INSERT INTO banking.customer
            (customer_id, full_name, birth_date, id_number, contact) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO NOTHING;""",
            (customer_id, full_name, birth_date, id_number, contact)
        )

# generate random data for accounts
def generate_account(cur):
    cur.execute("SELECT customer_id FROM banking.customer;")
    for (customer_id,) in cur.fetchall():
        for _ in range(random.randint(1, 3)):
            account_id = str(uuid.uuid4())
            acc_type = random.choice(["savings", "checking"])
            cur.execute("""
                INSERT INTO banking.account
                (account_id, customer_id, type, balance)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (account_id) DO NOTHING;""",
                (account_id, customer_id, acc_type, round(random.uniform(0, 1e8), 2))
            )

# generate random data for device
def generate_device(cur):
    cur.execute("SELECT customer_id FROM banking.customer;")
    for (customer_id,) in cur.fetchall():
        for _ in range(random.randint(1, 2)):
            device_id = str(uuid.uuid4())
            device_type = random.choice(["desktop", "mobile"])
            ip = fake.ipv4_public()
            cur.execute("""
                INSERT INTO banking.device
                (device_id, customer_id, device_type, ip_address)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (device_id) DO NOTHING;""",
                (device_id, customer_id, device_type, ip)
            )

# generate random transactions
def generate_transaction(cur, n=1000):
    cur.execute("SELECT ac.account_id, d.device_id \
                FROM banking.account ac\
                JOIN banking.device d ON d.customer_id = ac.customer_id;")
    rows = cur.fetchall()
    # generate a random transaction 
    for _ in range(n):
        tx_id = str(uuid.uuid4())
        account_id, device = random.choice(rows)
        
        # generate random device_id
        device_id = None
        
        # random amount between 10k and 10M
        amt = round(random.uniform(10_000, 15_000_000), 0)
        
        # choose transaction type
        tx_type = random.choices(['deposit', 'withdrawal', 'transfer'],
                                    weights=[0.2, 0.3, 0.5], k=1)[0]
        target_id = None
        if tx_type == 'withdrawal':     # withdrawal
            amt = -amt                  # negative for withdrawal
        if tx_type == 'transfer':       # transfer
            target_id = str(random.choice([a[0] for a in rows if a != account_id]))
            device_id = str(random.choices([device, uuid.uuid4()], weights=[0.8, 0.2], k=1)[0])
        
        cur.execute("""
            INSERT INTO banking.transaction
            (tx_id, account_id, device_id, target_id, amount, method, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (tx_id) DO NOTHING;""",
            (tx_id, account_id, device_id, target_id, amt,
             random.choice(['online', 'card', 'cash']),
             'pending')
        )
    

def main():
    conn = connect_db()
    with conn:
        cur = conn.cursor()

        # generate data
        generate_customer(cur, 1000)
        generate_account(cur)
        generate_device(cur)
        generate_transaction(cur, 1000)

        # commit changes and close connection
        conn.commit()
        cur.close()
    conn.close()
    print("Data generation completed successfully.")


if __name__ == "__main__":
    main()