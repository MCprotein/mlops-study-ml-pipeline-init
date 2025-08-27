# Airflow Docker Compose Management
.PHONY: up down restart logs test test-unit shell

# Start Airflow services
up:
	docker-compose up -d

# Stop Airflow services  
down:
	docker-compose down

# Restart Airflow services
restart:
	docker-compose down && docker-compose up -d

# View logs
logs:
	docker-compose logs -f

# Run tests in container
test:
	docker exec mlops-study-ml-pipeline-init-airflow-apiserver-1 bash -c "cd /opt/airflow && PYTHONPATH=/opt/airflow/dags:/opt/airflow python -m pytest tests/ -v"

# Run specific test file
test-unit:
	docker exec mlops-study-ml-pipeline-init-airflow-apiserver-1 bash -c "cd /opt/airflow && PYTHONPATH=/opt/airflow/dags:/opt/airflow python -m pytest tests/models/ineligible_loan_model/test_ineligible_loan_model.py -v"

# Open shell in container
shell:
	docker exec -it mlops-study-ml-pipeline-init-airflow-apiserver-1 bash

# Install pytest in container (one time setup)
setup-test:
	docker exec mlops-study-ml-pipeline-init-airflow-apiserver-1 pip install pytest