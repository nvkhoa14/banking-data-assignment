from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'banking-data',
    'depends_on_past': False,
    'start_date': datetime(2025, 7, 20),
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='banking_dq_workflow',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['banking','dq']
) as dag:

    t1_generate = BashOperator(
        task_id='generate_data',
        bash_command='python3 /opt/airflow/src/generate_data.py'
    )

    t2_quality = BashOperator(
        task_id='data_quality_checks',
        bash_command='python3 /opt/airflow/src/data_quality_standards.py'
    )

    t3_risk = BashOperator(
        task_id='monitoring',
        bash_command='python3 /opt/airflow/src/monitoring_audit.py'
    )

    # Define execution order
    t1_generate >> t2_quality >> t3_risk