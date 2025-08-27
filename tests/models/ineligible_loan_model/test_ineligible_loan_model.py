import unittest
from unittest.mock import Mock

from dags.support.date_values import DateValues
from tests import MockContext


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


if __name__ == "__main__":
    unittest.main()
