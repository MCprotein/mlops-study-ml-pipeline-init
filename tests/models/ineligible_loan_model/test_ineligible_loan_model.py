import os
import unittest
from pathlib import Path

from dags.support.date_values import DateValues
from tests import MockContext

os.environ["FEATURE_STORE_URL"] = "mysql://root:root@mariadb/mlops"
os.environ["MODEL_OUTPUT_HOME"] = str(
    Path(__file__).parent.parent.parent.parent / "dags/models/ineligible_loan_model"
)
home_dir = os.path.expanduser("~")
os.environ["MLOPS_DATA_STORE"] = f"{home_dir}/mlops_data_store"


class TestIneligibleLoanModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base_day = DateValues.get_before_one_day()

        cls.context = MockContext()

    def test_data_extract(self):
        # Given

        import dags.models.ineligible_loan_model.ineligible_loan_model as model

        # When
        model.data_extract.__setattr__(
            "sql",
            model.read_sql_file(model.sql_file_path).replace(
                '{{ macros.ds_add(ds, -1) | replace("-", "") }}', self.base_day
            ),
        )
        model.data_extract.execute(self.context)

    def test_data_preparation(self):
        # Given
        import dags.models.ineligible_loan_model.ineligible_loan_model as model
        from dags.models.ineligible_loan_model.data_preparation.preparation import (
            Preparation,
        )

        # When
        preparation = Preparation(
            model_name=model.model_name,
            model_version=model.model_version,
            base_day=self.base_day,
        )

        preparation.preprocessing()

    def test_data_preparation_of_dag_task(self):
        import dags.models.ineligible_loan_model.ineligible_loan_model as model

        # DockerOperator의 속성들이 올바르게 설정되었는지 테스트
        self.assertEqual(model.data_preparation.task_id, "데이터전처리")
        self.assertEqual(
            model.data_preparation.image, "ineligible_loan_model:pipeline-latest"
        )
        self.assertEqual(model.data_preparation.auto_remove, "success")
        self.assertEqual(
            model.data_preparation.docker_url, "unix://var/run/docker.sock"
        )
        self.assertEqual(model.data_preparation.network_mode, "mlops_study_network")
        self.assertEqual(model.data_preparation.mount_tmp_dir, False)

        # 환경변수가 올바르게 설정되었는지 테스트
        expected_env_keys = [
            "PYTHON_FILE",
            "MODEL_NAME",
            "MODEL_VERSION",
            "BASE_DAY",
            "PYTHONPATH",
            "MLOPS_DATA_STORE",
            "MODEL_OUTPUT_HOME",
            "FEATURE_STORE_URL",
        ]
        for key in expected_env_keys:
            self.assertIn(key, model.data_preparation.environment)

        # 볼륨 마운트가 올바르게 설정되었는지 테스트
        self.assertEqual(len(model.data_preparation.mounts), 1)
        mount = model.data_preparation.mounts[0]
        self.assertEqual(
            mount["Source"], "mlops-study-ml-pipeline-init_mlops_data_store"
        )
        self.assertEqual(mount["Target"], "/home/mlops/mlops_data_store")
        self.assertEqual(mount["Type"], "volume")

        # 명령어가 올바르게 설정되었는지 테스트
        if model.data_preparation.command:  # None 체크
            expected_command_parts = [
                "uv run python",
                "/home/mlops/data_preparation/preparation.py",
                "ineligible_loan_model",
                "1.0.0",
            ]
            for part in expected_command_parts:
                self.assertIn(part, model.data_preparation.command)

    def test_prediction(self):
        import dags.models.ineligible_loan_model.ineligible_loan_model as model
        from dags.models.ineligible_loan_model.prediction import Prediction

        prediction = Prediction(
            model_name=model.model_name,
            model_version=model.model_version,
            base_day=self.base_day,
        )

        prediction.predict()


if __name__ == "__main__":
    unittest.main()
