FROM python:3.10.9-slim
LABEL maintainer="mlops.study@gmail.com"

ARG USER_HOME=/home/mlops
ARG SUPPORT_SOURCE_PATH=support
ARG PREPARATION_SOURCE_PATH=models/ineligible_loan_model_ct/data_preparation
ARG REQUIREMENTS_PATH=models/ineligible_loan_model_ct/docker

# Install system dependencies for mysqlclient
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

RUN groupadd --gid 1000 mlops \
    && useradd --uid 1000 --gid mlops --shell /bin/bash --create-home mlops

# 종속성 파일만 먼저 복사 (캐시 최적화)
COPY --chown=mlops:mlops ${REQUIREMENTS_PATH}/pyproject.toml \
    ${USER_HOME}/
COPY --chown=mlops:mlops ${REQUIREMENTS_PATH}/.python-version \
    ${USER_HOME}/

USER mlops
WORKDIR ${USER_HOME}

# 종속성 설치 (캐시 활용)
RUN uv sync

# 나머지 파일 복사
COPY --chown=mlops:mlops ${SUPPORT_SOURCE_PATH}/ \
${USER_HOME}/support/
COPY --chown=mlops:mlops ${PREPARATION_SOURCE_PATH}/preparation.py \
${USER_HOME}/data_preparation/
RUN mkdir -p ${USER_HOME}/data_preparation ${USER_HOME}/mlops_data_store

WORKDIR ${USER_HOME}
