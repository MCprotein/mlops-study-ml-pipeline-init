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


if __name__ == "__main__":
    unittest.main()
