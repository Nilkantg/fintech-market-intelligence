.PHONY: help setup test lint deploy-producers submit-bronze submit-silver

PROJECT_ID   ?= fintech-market-intel
REGION       ?= us-central1
REPO         ?= $(REGION)-docker.pkg.dev/$(PROJECT_ID)/fintech-repo
BRONZE_BUCKET?= $(PROJECT_ID)-bronze
STAGING      ?= $(PROJECT_ID)-dataproc-staging

help:
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-25s %s\n", $$1, $$2}'

setup: ## Run one-time GCP project setup
	bash scripts/setup_gcp.sh

kafka-topics: ## Create Confluent Kafka topics
	bash scripts/setup_kafka_topics.sh

lint: ## Run ruff linter
	ruff check producers/ pipelines/ dags/ tests/

typecheck: ## Run mypy type checker
	mypy producers/ pipelines/ --ignore-missing-imports

test-unit: ## Run unit tests only (no GCP required)
	pytest tests/unit/ -m unit -v

test-integration: ## Run integration tests (requires dev GCP project)
	pytest tests/integration/ -m integration -v

test-all: ## Run all tests
	pytest tests/ -v

build-producers: ## Build all producer Docker images
	docker build -t $(REPO)/price-producer:latest -f infra/docker/price_producer/Dockerfile producers/price_producer/
	docker build -t $(REPO)/news-producer:latest   -f infra/docker/news_producer/Dockerfile    producers/news_producer/
	docker push $(REPO)/price-producer:latest
	docker push $(REPO)/news-producer:latest

deploy-producers: ## Deploy producers to Cloud Run
	gcloud run deploy price-producer \
		--image=$(REPO)/price-producer:latest \
		--region=$(REGION) --min-instances=1 --max-instances=1 \
		--service-account=producer-sa@$(PROJECT_ID).iam.gserviceaccount.com \
		--set-env-vars="GCP_PROJECT_ID=$(PROJECT_ID)" \
		--no-allow-unauthenticated

submit-bronze: ## Submit Bronze streaming job to Dataproc Serverless
	bash scripts/submit_dataproc_job.sh bronze pipelines/bronze/kafka_to_gcs_prices.py

submit-silver: ## Submit Silver batch job to Dataproc Serverless
	bash scripts/submit_dataproc_job.sh silver pipelines/silver/gcs_to_bq_prices.py

tf-init: ## Terraform init
	cd infra/terraform && terraform init

tf-plan: ## Terraform plan
	cd infra/terraform && terraform plan -var="project_id=$(PROJECT_ID)"

tf-apply: ## Terraform apply
	cd infra/terraform && terraform apply -var="project_id=$(PROJECT_ID)" -auto-approve
