from datetime import datetime
from pathlib import Path

import pendulum
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
from support.callback_function import failure_callback, success_callback

local_timezone = pendulum.timezone("Asia/Seoul")
conn_id = "feature_store"
model_name = "ineligible_loan_model"
model_version = "1.0.0"


# Get the directory where this DAG file is located
dag_dir = Path(__file__).parent
sql_file_path = dag_dir / "data_extract" / "features.sql"


def read_sql_file(file_path):
    with open(file_path, "r") as file:
        sql_query_lines = file.read()
    return "".join(sql_query_lines)


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
    # data_extract = EmptyOperator(task_id="데이터추출")
    data_extract = SQLExecuteQueryOperator(
        task_id="데이터추출",
        conn_id=conn_id,
        sql=read_sql_file(sql_file_path),
        split_statements=True,
    )

    data_preparation = DockerOperator(
        task_id="데이터전처리",
        image="ineligible_loan_model:pipeline-latest",
        container_name="ineligible_loan_model_pipeline_{{ ds_nodash }}_{{ ts_nodash }}",
        auto_remove="success",
        docker_url="unix://var/run/docker.sock",
        network_mode="mlops_study_network",
        mount_tmp_dir=False,
        environment={
            "PYTHON_FILE": "/home/mlops/data_preparation/preparation.py",
            "MODEL_NAME": model_name,
            "BASE_DAY": "{{ macros.ds_add(ds, -1) | replace('-', '') }}",
            "PYTHONPATH": "/home/mlops",
            "MLOPS_DATA_STORE": "/home/mlops/mlops_data_store",
            "MODEL_OUTPUT_HOME": "/home/mlops",
            "FEATURE_STORE_URL": "mysql://root:root@mariadb/mlops",
        },
        mounts=[
            Mount(
                source="mlops-study-ml-pipeline-init_mlops_data_store",
                target="/home/mlops/mlops_data_store",
                type="volume",
            )
        ],
        command="uv run python /home/mlops/data_preparation/preparation.py "
        + model_name
        + " "
        + model_version
        + " {{ macros.ds_add(ds, -1) | replace('-', '') }}",
    )

    prediction = DockerOperator(
        task_id="예측",
        image="ineligible_loan_model:pipeline-latest",
        container_name="ineligible_loan_model_pipeline_{{ ds_nodash }}_{{ ts_nodash }}",
        auto_remove="success",
        docker_url="unix://var/run/docker.sock",
        network_mode="mlops_study_network",
        mount_tmp_dir=False,
        environment={
            "PYTHON_FILE": "/home/mlops/model/prediction.py",
            "MODEL_NAME": model_name,
            "MODEL_VERSION": model_version,
            "BASE_DAY": "{{ macros.ds_add(ds, -1) | replace('-', '') }}",
            "PYTHONPATH": "/home/mlops",
            "MLOPS_DATA_STORE": "/home/mlops/mlops_data_store",
            "MODEL_OUTPUT_HOME": "/home/mlops",
            "FEATURE_STORE_URL": "mysql://root:root@mariadb/mlops",
        },
        mounts=[
            Mount(
                source="mlops-study-ml-pipeline-init_mlops_data_store",
                target="/home/mlops/mlops_data_store",
                type="volume",
            )
        ],
        command="uv run python /home/mlops/model/prediction.py "
        + model_name
        + " "
        + model_version
        + " {{ macros.ds_add(ds, -1) | replace('-', '') }}",
    )

    data_extract >> data_preparation >> prediction
