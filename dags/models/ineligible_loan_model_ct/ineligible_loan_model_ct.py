from datetime import datetime
from pathlib import Path

import pendulum
from airflow import DAG
from airflow.models import Variable
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.empty import EmptyOperator

from dags.models.ineligible_loan_model.ineligible_loan_model import data_preparation
from dags.support.callback_function import failure_callback, success_callback

local_timezone = pendulum.timezone("Asia/Seoul")
conn_id = "feature_store"
dag_dir = Path(__file__).parent
sql_file_path = dag_dir / "data_extract" / "features.sql"


def read_sql_file(file_path):
    with open(file_path, "r") as file:
        sql_query_lines = file.read()
    return "".join(sql_query_lines)


with DAG(
    dag_id="ineligible_loan_model_ct",
    default_args={
        "owner": "mlops.study",
        "depends_on_past": False,
        "email": ["mlops.study@gmail.com"],
        "on_failure_callback": failure_callback,
        "on_success_callback": success_callback,
    },
    description="부적격대출모델CT",
    schedule=None,
    start_date=datetime(2023, 5, 1, tzinfo=local_timezone),
    catchup=False,
    tags=["mlops", "study"],
) as dag:
    data_extract = SQLExecuteQueryOperator(
        task_id="데이터추출",
        conn_id=conn_id,
        sql=read_sql_file(sql_file_path),
        split_statements=True,
    )

    data_preparation = EmptyOperator(task_id="데이터전처리")

    training = EmptyOperator(task_id="모델학습및모델평가")

    data_extract >> data_preparation >> training
