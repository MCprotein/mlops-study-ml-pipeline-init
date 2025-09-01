import os
import sys

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression

from dags.models.ineligible_loan_model.ineligible_loan_model import data_preparation

feature_store_url = os.getenv("FEATURE_STORE_URL", "")
model_output_home = os.getenv("MODEL_OUTPUT_HOME", "")
mlops_data_store = os.getenv("MLOPS_DATA_STORE", "")


class Prediction:
    def __init__(self, model_name: str, model_version: str, base_day: str):
        self._model_name = model_name
        self._model_version = model_version
        self._base_day = base_day

    def _get_encoded_features(self):
        data_preparation_data_path = f"{mlops_data_store}/data_preparation/{self._model_name}/{self._model_version}/{self._base_day}"

        feature_df = pd.read_csv(
            f"{data_preparation_data_path}/{self._model_name}_{self._model_version}.csv"
        )
        print(feature_df)
        return feature_df

    def _load_model(self):
        model_file_name = f"{self._model_name}.joblib"
        logistic_model: LogisticRegression = joblib.load(
            f"{model_output_home}/model_output/{model_file_name}"
        )

        print(logistic_model)
        return logistic_model

    def _predict(
        self,
        feature_df: pd.DataFrame,
        logistic_model: LogisticRegression,
        x_pred,
    ):
        print(logistic_model.classes_)

        predict = logistic_model.predict(x_pred)
        print("Target on test data (sample 20) = ", predict[:20])

        test_predict_proba = logistic_model.predict_proba(x_pred)
        print(f"test_predict_proba (sample 5) = {test_predict_proba[:5]}")

        test_probabilities = pd.DataFrame(test_predict_proba)[1].to_list()
        print(f"test_probabilities (sample 5) = {test_probabilities[:5]}")

        data = {
            "base_dt": self._base_day,
            "applicant_id": feature_df["applicant_id"].to_list(),
            "predict": predict,
            "probability": test_probabilities,
        }

        test_predicted = pd.DataFrame(data=data)
        print(f"test_predicted = {test_predicted}")
        return test_predicted

    def _save_to_table(self, test_predicted: pd.DataFrame):
        from sqlalchemy import create_engine
        from sqlalchemy.engine import Engine

        engine: Engine = create_engine(feature_store_url)
        with engine.connect() as conn:
            init_sql = f"""
            delete
                from mlops.ineligible_loan_model_result
            where base_dt = '{self._base_day}'
            """
            conn.execute(statement=init_sql)
            insert_rows = test_predicted.to_sql(
                name="ineligible_loan_model_result",
                con=conn,
                schema="mlops",
                if_exists="append",
                index=False,
            )
            print(f"insert_rows = {insert_rows}")

    def predict(self):
        features = [
            "gender",
            "family_dependents",
            "education",
            "applicant_income",
            "coapplicant_income",
            "loan_amount_term",
            "credit_history",
            "property_area",
            "married_No",
            "married_Yes",
            "self_employed_No",
            "self_employed_Yes",
        ]

        feature_df = self._get_encoded_features()

        x_pred = feature_df[features].values

        logistic_model = self._load_model()

        test_predicted = self._predict(feature_df, logistic_model, x_pred)

        self._save_to_table(test_predicted)


if __name__ == "__main__":
    print(f"sys.argv= {sys.argv}")
    if len(sys.argv) != 4:
        print("Insufficient arguments.")
        sys.exit(1)

    model_name = sys.argv[1]
    model_version = sys.argv[2]
    base_day = sys.argv[3]
    print(model_name, model_version, base_day)

    prediction = Prediction(
        model_name=model_name, model_version=model_version, base_day=base_day
    )
    prediction.predict()
