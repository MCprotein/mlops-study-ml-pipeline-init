class Prediction:
    def __init__(self, model_name: str, model_version: str, base_day: str):
        self._model_name = model_name
        self._model_version = model_version
        self._base_day = base_day

    def predict(self):
        print("predict!!!")
