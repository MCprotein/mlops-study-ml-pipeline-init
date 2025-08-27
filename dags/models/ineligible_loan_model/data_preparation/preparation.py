import os
from typing import Dict

import joblib
import pandas as pd

feature_store_url = os.getenv("FEATURE_STORE_URL", "")
model_output_home = os.getenv("MODEL_OUTPUT_HOME", "")


class Preparation:
    _model_name: str
    _model_version: str
    _base_day: str

    def __init__(self, model_name: str, model_version: str, base_day: str) -> None:
        self.model_name = model_name
        self._model_version = model_version
        self._base_day = base_day

    def preprocessing(self):
        ## 1. 데이터 추출
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import Engine

        engine: Engine = create_engine(feature_store_url)

        # 데이터 추출 결과 조회
        sql = f"""
        select *
          from mlops.ineligible_loan_model_features
         where base_dt = '{self._base_day}'
        """
        with engine.connect() as conn:
            loan_df = pd.read_sql(text(sql), con=conn)

        # 2. 데이터 전처리

        """
        결측치(N/A) 제거
        - family_dependents와 loan_amount_term의 결측치를 채우는 작업을 수행한다.
        'fillna'는 결측치를 채우는 메서드이며, 'inplace=True'는 원본 데이터프레임을 직접 수정함을 의미한다.
        - loan_amount_term은 데이터 과학자가 대출서비스에서 발생하는 대출기간의 기본값은 60개월로 설정하므로
          결측값을 60으로 채웠다.
        """

        # family_dependents
        loan_df["family_dependents"].fillna("0", inplace=True)

        # loan_amount_term
        loan_df["loan_amount_term"].fillna("60", inplace=True)

        """
        Replace 변환
        - 범주형(Categorical) 변수 중 gender, education을 숫자형 변수로 변환한다.
        - 이와 같이 변환하는 방법에는 다음에 소개할 원핫 인코딩 (One-Hot Encoding),
          라벨 인코딩(Label Encoding) 등이 있지만, 간단히 replace 함수를 사용하여, 0과 1로 변환하였다.
        """

        # gender
        loan_df.gender = loan_df.gender.replace({"Male": 1, "Female": 0})

        # education
        loan_df.education = loan_df.education.replace(
            {"Graduate": 1, "Not Graduate": 0}
        )

        """
        원핫 인코딩 (One-Hot Encoding)
        - one_hot_encoder 불러오기
        - 훈련된 인코더를 사용하여 데이터를 원핫 인코딩한다.
            - get_feature_names_out 메소드를 이용하여 원핫 인코딩된 컬럼명을 가져올 수 있다.
            - 컬럼명 array : array(['married_No', 'married_Yes', 'self_employed_No',
                                'self_employed_Yes'], dtype=object)
        - 기존 피처 컬럼 삭제
            - 원래 데이터를 가지고 있는 'married', 'self_employed' 컬럼을 삭제한다.
        """

        from sklearn.preprocessing import OneHotEncoder

        one_hot_features = ["married", "self_employed"]

        # one_hot_encoder 불러오기
        one_hot_encoder: OneHotEncoder = joblib.load(
            f"{model_output_home}/model_output/one_hot_encoder.joblib"
        )

        # 원핫 인코딩된 컬럼명 조회
        encoded_feature_names = one_hot_encoder.get_feature_names_out(one_hot_features)

        # 원핫 인코딩
        one_hot_encoded_data = one_hot_encoder.transform(
            loan_df[one_hot_features]
        ).toarray()
        loan_encoded_df = pd.DataFrame(
            data=one_hot_encoded_data, columns=encoded_feature_names
        )
        loan_df = pd.concat([loan_df, loan_encoded_df], axis=1)

        # 기존 피처 컬럼 삭제
        loan_df = loan_df.drop(columns=one_hot_features)

        """
        라벨 인코딩 (Label Encoding)
        - label_encoders 불러오기
        - 훈련된 인코더를 사용하여 데이터를 라벨 인코딩하고 기존 컬럼에 저장한다.
        """
        from sklearn.preprocessing import LabelEncoder

        categorical_features = ["property_area", "family_dependents"]

        # label_encoders 불러오기
        label_encoders: Dict[str, LabelEncoder] = joblib.load(
            f"{model_output_home}/model_output/label_encoders.joblib"
        )

        # 라벨 인코딩
        for categorical_feature in categorical_features:
            label_encoder = label_encoders[categorical_feature]
            print(f"categorical_feature = {categorical_feature}")
            print(f"label_encoder.classes_ = {label_encoder.classes_}")

            loan_df[categorical_feature] = label_encoder.transform(
                loan_df[categorical_feature]
            )
