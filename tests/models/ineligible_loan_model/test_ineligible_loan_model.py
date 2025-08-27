import os
import unittest
from pathlib import Path

from dags.support.date_values import DateValues
from tests import MockContext

os.environ["FEATURE_STORE_URL"] = "mysql://root:root@mariadb/mlops"
os.environ["MODEL_OUTPUT_HOME"] = str(
    Path(__file__).parent.parent.parent.parent / "dags/models/ineligible_loan_model"
)


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


if __name__ == "__main__":
    unittest.main()
