from unittest.mock import Mock


class MockContext(Mock):
    def __init__(self):
        super().__init__()
        self.task = {"email": "mlops.study@gmail.com", "owner": "mlops.study"}
