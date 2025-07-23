from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

from generate_data import generate_transaction

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    dag_id='generate_transaction_every_minute',
    default_args=default_args,
    description='Call generate_transaction() every minute',
    schedule_interval=timedelta(minutes=1),  # or schedule_interval='* * * * *'
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
) as dag:

    run_transaction = PythonOperator(
        task_id='run_generate_transaction',
        python_callable=generate_transaction,   
        op_kwargs={'n': 1000},                 
    )
    run_prosessing = BashOperator(
        task_id='run_processing',
        bash_command='python3 /opt/airflow/src/monitoring_audit.py'
    )
    run_transaction >> run_prosessing
