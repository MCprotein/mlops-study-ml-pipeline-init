import os
import unittest
from pathlib import Path

from dags.support.date_values import DateValues
from tests import MockContext

os.environ["FEATURE_STORE_URL"] = "mysql://root:root@mariadb/mlops"
os.environ["MODEL_OUTPUT_HOME"] = str(
    Path(__file__).parent.parent.parent.parent / "dags/models/ineligible_loan_model"
)
home_dir = "/home/mlops"  # 기존 모델과 일치
os.environ["MLOPS_DATA_STORE"] = f"{home_dir}/mlops_data_store"


class TestIneligibleLoanModelCt(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base_day = DateValues.get_current_date()
        cls.base_ym = DateValues.get_before_one_month(cls.base_day)
        cls.context = MockContext()

    def test_data_extract(self):
        # Given
        import dags.models.ineligible_loan_model_ct.ineligible_loan_model_ct as model

        # When
        model.data_extract.__setattr__(
            "sql",
            model.read_sql_file(model.sql_file_path).replace(
                "{{  ds_nodash  }}", self.base_day
            ),
        )
        model.data_extract.execute(self.context)

    def test_data_preparation(self):
        # Given
        import dags.models.ineligible_loan_model_ct.ineligible_loan_model_ct as model
        from dags.models.ineligible_loan_model_ct.data_preparation.preparation import (
            Preparation,
        )

        # When
        preparation = Preparation(
            model_name=model.model_name,
            base_day=self.base_ym,
        )

        preparation.preprocessing()

    def test_data_preparation_of_dag_task(self):
        import dags.models.ineligible_loan_model_ct.ineligible_loan_model_ct as model

        env = {
            "PYTHON_FILE": "/home/mlops/data_preparation/preparation.py",
            "MODEL_NAME": "ineligible_loan_model",
            "MODEL_VERSION": "1.0.0",
            "BASE_DAY": "20250905",
        }

        model.data_preparation.__setattr__("env", env)
        model.data_preparation.container_name = (
            f"test_data_preparation_ct_{self.base_day}"
        )
        model.data_preparation.command = (
            f"uv run python /home/mlops/data_preparation/preparation.py {model.model_name} "
            f"{self.base_day}"
        )
        model.data_preparation.execute(self.context)

    def test_training(self):
        # Given
        import dags.models.ineligible_loan_model_ct.ineligible_loan_model_ct as model
        from dags.models.ineligible_loan_model_ct.model.training import Training

        ct_model_version = "1.0.0"

        # When
        training = Training(
            model_name=model.model_name,
            model_version=ct_model_version,
            base_day=self.base_ym,
        )

        training.train()


if __name__ == "__main__":
    unittest.main()
