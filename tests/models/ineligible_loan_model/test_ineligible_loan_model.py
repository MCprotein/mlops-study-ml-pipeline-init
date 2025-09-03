import os
import unittest
from pathlib import Path

from dags.support.date_values import DateValues
from tests import MockContext

os.environ["FEATURE_STORE_URL"] = "mysql://root:root@mariadb/mlops"
os.environ["MODEL_OUTPUT_HOME"] = str(
    Path(__file__).parent.parent.parent.parent / "dags/models/ineligible_loan_model"
)
# home_dir = os.path.expanduser("~")
home_dir = "/home/mlops"
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

        env = {
            "PYTHON_FILE": "/home/mlops/data_preparation/preparation.py",
            "MODEL_NAME": model.model_name,
            "MODEL_VERSION": model.model_version,
            "BASE_DAY": self.base_day,
        }
        model.data_preparation.__setattr__("env", env)
        model.data_preparation.container_name = f"test_data_preparation_{self.base_day}"
        model.data_preparation.command = (
            f"uv run python /home/mlops/data_preparation/preparation.py {model.model_name} "
            f"{model.model_version} {self.base_day}"
        )
        model.data_preparation.execute(self.context)

    def test_prediction(self):
        import dags.models.ineligible_loan_model.ineligible_loan_model as model
        from dags.models.ineligible_loan_model.model.prediction import Prediction

        prediction = Prediction(
            model_name=model.model_name,
            model_version=model.model_version,
            base_day=self.base_day,
        )

        prediction.predict()

    def test_prediction_of_dag_task(self):
        import dags.models.ineligible_loan_model.ineligible_loan_model as model

        env = {
            "PYTHON_FILE": "/home/mlops/model/prediction.py",
            "MODEL_NAME": model.model_name,
            "MODEL_VERSION": model.model_version,
            "BASE_DAY": self.base_day,
        }
        model.prediction.__setattr__("env", env)
        model.prediction.container_name = f"test_prediction_{self.base_day}"
        model.prediction.command = (
            f"uv run python /home/mlops/model/prediction.py {model.model_name} \
          {model.model_version} {self.base_day}"
        )
        model.prediction.execute(self.context)


if __name__ == "__main__":
    unittest.main()
