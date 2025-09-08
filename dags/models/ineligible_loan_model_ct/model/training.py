import os
import sys

import joblib
import pandas as pd

mlops_data_store = os.getenv("MLOPS_DATA_STORE", "")


class Training:
    def __init__(self, model_name: str, model_version: str, base_day: str):
        self._model_name = model_name
        self._model_version = model_version
        self._base_day = base_day
        self._data_preparation_path = f"{mlops_data_store}/data_preparation/{self._model_name}/ct/{self._base_day}"
        self._model_output_path = f"{mlops_data_store}/model/{self._model_name}/{self._model_version}/{self._base_day}"
        self._makedir()

    def _makedir(self):
        if not os.path.isdir(self._model_output_path):
            os.makedirs(self._model_output_path)

    def train(self):
        loan_df = pd.read_csv(f"{self._data_preparation_path}/{self._model_name}.csv")
        print(f"len(loan_df) = {len(loan_df)}")

        ###########################################################################
        ## 3. 모델 학습
        ###########################################################################
        from sklearn.linear_model import LogisticRegression
        from support.model.evaluation.lift import Lift

        """
        Train, Test 데이터셋 분리
        """
        # random 처리 시 항상 동일한 결과를 생성될 수 있도록, random_state값을 설정한다.
        random_state = 100
        # 일반적으로 데이터를 학습 세트와 테스트 세트로 나누는 과정에서 무작위성을 도입한다.
        # "random_state" 값이 동일하면 항상 학습 세트와 테스트 세트에서 정확하게 동일한 데이터를 얻게 된다.
        # 이는 실험의 재현성과 결과의 일관성을 보장하기 위해서 사용된다.
        from pandas.core.frame import DataFrame

        loan_train: DataFrame = loan_df.sample(frac=0.65, random_state=random_state)
        loan_test: DataFrame = loan_df.drop(loan_train.index.tolist())

        # index 재설정
        loan_train = loan_train.reset_index(drop=True)
        loan_test = loan_test.reset_index(drop=True)

        ## 결과 확인
        print("######### loan_train #########")
        loan_train.info()
        print("\n######### loan_test #########")
        loan_test.info()

        ## 모델 피처와 타겟
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
        target = "loan_status"

        x_train = loan_train[features].values
        y_train = loan_train[target].values

        x_test = loan_test[features].values
        y_test = loan_test[target].values

        ## 모델 학습
        logistic_model = LogisticRegression(max_iter=100)

        logistic_model.fit(x_train, y_train)

        ## 로지스틱회귀 모델학습 결과확인
        # 학습모델의 coefficient(계수)확인
        # coefficient : 각 피처의 가중치(weight)를 나타내는 벡터 - 해당 피처가 예측값에 미치는 영향의 크기
        # 양수이면 증가할수록 대출 디폴트 가능성을 높인다.
        # 음수이면 증가할수록 대출 디폴트 가능성을 낮춘다.
        print("Coefficient of model :", logistic_model.coef_)
        # 학습모델의 intercept(절편)확인
        # intercept : 모델의 예측값을 0으로 만드는 값 - 모든 피처가 0일 때의 예측값
        print("Intercept of model", logistic_model.intercept_)

        # 학습모델의 정확도 확인
        print("Accuracy of model", logistic_model.score(x_train, y_train))

        # 모델학습(Train 데이터셋) Lift 결과확인
        # probabilities : 모델이 예측한 대출 디폴트 가능성
        train_predict_proba = logistic_model.predict_proba(x_train)
        # logistic_model.classes_ : 모델이 예측한 대출 디폴트 가능성의 클래스 목록
        # 0 : 대출 디폴트 불가능
        # 1 : 대출 디폴트 가능
        # 모델이 예측한 대출 디폴트 가능성의 클래스 목록을 리스트로 변환
        train_probabilities = pd.DataFrame(train_predict_proba)[1].to_list()
        # labels : 실제 대출 디폴트 가능성
        # cut_count : 데이터를 10개의 구간으로 나누어 각 구간의 Lift 값을 계산
        train_lift = Lift(
            probabilities=train_probabilities, labels=y_train.tolist(), cut_count=10
        )
        # 모델학습(Train 데이터셋) Lift 결과확인
        print(f"{train_lift.get_cum_lift()}")

        # cut_code가 0인 경우가 상위 10% 확률값으로 가장 큰 구간을 의미하며,
        # 무작위로 선택하는 것보다 대략 3.6배의 나은 결과를 얻을 수 있음을 의미한다.

        # 모델학습(Train 데이터셋) Accuracy 결과확인
        score = logistic_model.score(x_train, y_train)
        print("accuracy_score overall :", score)
        print("accuracy_score percent :", round(float(score) * 100, 2))

        ###########################################################################
        ## 4. 모델 예측
        ###########################################################################
        # logistic_model의 분류값 확인
        print(f"logistic_model.classes_ = {logistic_model.classes_}")

        # 테스트 데이터셋의 모델예측 라벨데이터 추출
        test_predict = logistic_model.predict(x_test)
        print("Target on test data (sample 20) =", test_predict[:20])

        # 테스트 데이터셋의 모델예측 probability(확률) 추출
        test_predict_proba = logistic_model.predict_proba(x_test)
        print(f"test_predict_proba (sample 5) = {test_predict_proba[:5]}")

        # 예측 라벨이 1인 경우의 probability 추출
        test_probabilities = pd.DataFrame(test_predict_proba)[1].to_list()
        print(f"test_probabilities (sample 5) = {test_probabilities[:5]}")

        # 모델학습(Test 데이터셋)의 Lift 결과확인
        test_lift = Lift(
            probabilities=test_probabilities, labels=y_test.tolist(), cut_count=10
        )
        print(f"{test_lift.get_cum_lift()}")

        # 모델학습(Test 데이터셋) Accuracy 결과확인
        score = logistic_model.score(x_test, y_test)
        print("accuracy_score overall :", score)
        print("accuracy_score percent :", round(float(score) * 100, 2))

        ###########################################################################
        ## 5. 모델 저장
        ###########################################################################
        # 모델파일을 로컬 저장소에 저장
        model_file_name = f"{self._model_name}.joblib"

        # 모델 저장
        joblib.dump(logistic_model, f"{self._model_output_path}/{model_file_name}")

        # 모델 불러오기
        # logistic_model = joblib.load(f"./model_output/{model_file_name}")


if __name__ == "__main__":
    print(f"sys.argv = {sys.argv}")

    if len(sys.argv) != 3:
        print("Insufficient arguments.")
        sys.exit(1)
    from support.date_values import DateValues

    _model_name = sys.argv[1]
    _base_day = sys.argv[2]
    _model_version = "1.0.0"
    _base_ym = DateValues.get_before_one_month(_base_day)

    print(f"_model_name = {_model_name}")
    print(f"_base_day = {_base_day}")
    print(f"_model_version = {_model_version}")
    print(f"_base_ym = {_base_ym}")

    training = Training(
        model_name=_model_name, model_version=_model_version, base_day=_base_ym
    )

    training.train()
