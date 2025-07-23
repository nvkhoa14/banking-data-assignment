# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: banking-postgres image
# ─────────────────────────────────────────────────────────────────────────────
FROM postgres:13 AS banking-postgres

# inject your schema and init scripts
COPY sql/schema.sql              /docker-entrypoint-initdb.d/
COPY sql/01-init.sh              /docker-entrypoint-initdb.d/

ENV POSTGRES_DB=banking \
    POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=secret

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: airflow-banking image
# ─────────────────────────────────────────────────────────────────────────────
FROM apache/airflow:2.5.1-python3.9 AS airflow-banking

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libpq-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python requirements
COPY requirements.txt /opt/airflow/requirements.txt
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt

# Copy your scripts & DAGs
COPY src/  /opt/airflow/scripts/
COPY airflow/dags/     /opt/airflow/dags/

ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
EXPOSE 8080