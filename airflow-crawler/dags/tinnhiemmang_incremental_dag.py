from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "you",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="tinnhiemmang_incremental_daily",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval="0 8 * * *",  # 8h sáng mỗi ngày
    catchup=False,
    tags=["crawl", "open-source"],
) as dag:

    run_incremental = BashOperator(
        task_id="run_incremental",
        bash_command="python /opt/airflow/crawl_incremental_pg.py"
    )

    run_incremental

