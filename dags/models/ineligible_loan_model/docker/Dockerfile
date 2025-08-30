FROM python:3.10.9-slim
LABEL maintainer="mlops.study@gmail.com"

ARG USER_HOME=/home/mlops
ARG PREPARATION_SOURCE_PATH=data_preparation
ARG MODEL_OUTPUT=model_output
ARG REQUIREMENTS_PATH=docker

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

RUN mkdir -p ${USER_HOME}/data_preparation
COPY --chown=mlops:mlops ${PREPARATION_SOURCE_PATH}/preparation.py \
    ${USER_HOME}/data_preparation/
COPY --chown=mlops:mlops ${MODEL_OUTPUT}/ \
    ${USER_HOME}/model_output/
COPY --chown=mlops:mlops ${REQUIREMENTS_PATH}/pyproject.toml \
    ${USER_HOME}/
COPY --chown=mlops:mlops ${REQUIREMENTS_PATH}/.python-version \
    ${USER_HOME}/

USER mlops
WORKDIR ${USER_HOME}
RUN mkdir -p ${USER_HOME}/mlops_data_store \
    && uv sync --no-cache

WORKDIR ${USER_HOME}
