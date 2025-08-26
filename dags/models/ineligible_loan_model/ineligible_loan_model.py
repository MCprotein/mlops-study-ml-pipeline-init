from datetime import datetime

import pendulum
from airflow import DAG
from airflow.providers.standard.operators.empty import EmptyOperator
from support.callback_function import failure_callback, success_callback

local_timezone = pendulum.timezone("Asia/Seoul")

with DAG(
    dag_id="ineligible_loan_model",
    default_args={
        "owner": "mlops.study",
        "depends_on_past": False,
        "email": ["mlops.study@gmail.com"],
        "on_failure_callback": failure_callback,
        "on_success_callback": success_callback,
    },
    description="부적격대출모델",
    schedule=None,
    start_date=datetime(2023, 5, 1, tzinfo=local_timezone),
    catchup=False,
    tags=["mlops", "study"],
) as dag:
    data_extract = EmptyOperator(task_id="데이터추출")

    data_preparation = EmptyOperator(task_id="데이터전처리")

    prediction = EmptyOperator(task_id="예측")

    data_extract >> data_preparation >> prediction
