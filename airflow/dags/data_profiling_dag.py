from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def test_task():
    print("Airflow is working perfectly for Xuchen!")

with DAG(
    dag_id='01_hello_airflow',
    start_date=datetime(2026, 3, 1),
    schedule_interval=None, # 手动触发
    catchup=False
) as dag:
    task = PythonOperator(
        task_id='hello_task',
        python_callable=test_task
    )
