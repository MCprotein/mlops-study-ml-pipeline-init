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

# Run specific test (usage: make unittest [ClassName.method_name or test_name])
# Examples: 
#   make unittest                                    # run all tests
#   make unittest TestIneligibleLoanModel.test_data_extract   # run specific class.method
#   make unittest TestIneligibleLoanModel            # run specific test class
unittest:
	@if [ -z "$(word 2,$(MAKECMDGOALS))" ]; then \
		docker exec mlops-study-ml-pipeline-init-airflow-apiserver-1 bash -c "cd /opt/airflow && PYTHONPATH=/opt/airflow/dags:/opt/airflow python -m pytest tests/ -v -s"; \
	elif echo "$(word 2,$(MAKECMDGOALS))" | grep -q "\\."; then \
		CLASS=$$(echo "$(word 2,$(MAKECMDGOALS))" | cut -d'.' -f1); \
		METHOD=$$(echo "$(word 2,$(MAKECMDGOALS))" | cut -d'.' -f2); \
		docker exec mlops-study-ml-pipeline-init-airflow-apiserver-1 bash -c "cd /opt/airflow && PYTHONPATH=/opt/airflow/dags:/opt/airflow python -m pytest tests/ -k \"$$CLASS and $$METHOD\" -v -s"; \
	else \
		docker exec mlops-study-ml-pipeline-init-airflow-apiserver-1 bash -c "cd /opt/airflow && PYTHONPATH=/opt/airflow/dags:/opt/airflow python -m pytest tests/ -k \"$(word 2,$(MAKECMDGOALS))\" -v -s"; \
	fi

# Dummy target to handle test name argument
%:
	@:

# Open shell in container
shell:
	docker exec -it mlops-study-ml-pipeline-init-airflow-apiserver-1 bash

# Install pytest in container (one time setup)
setup-test:
	docker exec mlops-study-ml-pipeline-init-airflow-apiserver-1 pip install pytest