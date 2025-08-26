import unittest

from airflow.sdk.bases.operator import BaseOperator
from airflow.sdk.definitions.context import Context


class TestIneligibleLoanModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Common Given
        cls.base_day = "20250826"

        class ContextTask:
            email = "mlops.study@gmail.com"
            owner = "mlops.study"

        operator = BaseOperator(
            task_id="test", email="mlops.study@gmail.com", owner="mlops.study"
        )

        # cls.context = {"task": ContextTask()}
        context = Context(task=operator)
        cls.context = context

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


if __name__ == "__main__":
    unittest.main()
