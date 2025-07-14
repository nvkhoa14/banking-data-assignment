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
                (account_id, customer_id, type, status, balance)
                VALUES (%s,%s,%s,'active',%s)
                ON CONFLICT (account_id) DO NOTHING;""",
                (account_id, customer_id, acc_type, round(random.uniform(0, 1e7), 2))
            )

# generate random data for devic
def generate_device(cur):
    cur.execute("SELECT customer_id FROM banking.customer;")
    for (customer_id,) in cur.fetchall():
        for _ in range(random.randint(1, 2)):
            device_id = str(uuid.uuid4())
            device_type = random.choice(["desktop", "mobile"])
            ip = fake.ipv4_public()
            lat, lon = fake.latitude(), fake.longitude()
            trust_score = random.randint(0, 100)
            cur.execute("""
                INSERT INTO banking.device
                (device_id, customer_id, device_type, ip_address, geo_lat, geo_lon, trust_score)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (device_id) DO NOTHING;""",
                (device_id, customer_id, device_type, ip, lat, lon, trust_score)
            )

def main():
    conn = connect_db()
    with conn:
        cur = conn.cursor()

        # generate data
        generate_customer(cur, 1000)
        generate_account(cur)
        generate_device(cur)

        # commit changes and close connection
        conn.commit()
        cur.close()
    conn.close()
    print("Data generation completed successfully.")


if __name__ == "__main__":
    main()