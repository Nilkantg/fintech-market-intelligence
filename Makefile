.PHONY: help setup lint typecheck test-unit test-integration \
        build-producers deploy-producers \
        submit-bronze submit-silver tf-init tf-plan tf-apply

# ── Read .env if it exists ─────────────────────────────────────
-include .env
export

PROJECT_ID   ?= fintech-market-intel
REGION       ?= us-central1
IMAGE_REPO    = $(REGION)-docker.pkg.dev/$(PROJECT_ID)/fintech-repo

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS=":.*?## "}; {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}'

# ── Local dev ─────────────────────────────────────────────────
setup: ## Install dev dependencies
	pip install ruff mypy pytest pytest-cov \
	  pyspark==3.5.0 confluent-kafka finnhub-python \
	  google-cloud-bigquery google-cloud-storage \
	  google-cloud-secret-manager great-expectations

lint: ## Lint with ruff
	ruff check producers/ pipelines/ dags/ config/ tests/

typecheck: ## Type check with mypy
	mypy producers/ pipelines/ config/ --ignore-missing-imports

test-unit: ## Run unit tests (no GCP required)
	pytest tests/unit/ -m unit -v

test-integration: ## Run integration tests (requires GCP)
	pytest tests/integration/ -m integration -v

test-all: ## Run all tests
	pytest tests/ -v --cov=pipelines --cov=producers --cov-report=term-missing

# ── Docker / Cloud Run ────────────────────────────────────────
build-price-producer: ## Build price producer image
	docker build \
	  -t $(IMAGE_REPO)/price-producer:latest \
	  -f infra/docker/price_producer/Dockerfile \
	  producers/price_producer/

push-price-producer: build-price-producer ## Push to Artifact Registry
	docker push $(IMAGE_REPO)/price-producer:latest

deploy-price-producer: push-price-producer ## Deploy to Cloud Run
	gcloud run deploy price-producer \
	  --image=$(IMAGE_REPO)/price-producer:latest \
	  --region=$(REGION) \
	  --service-account=producer-sa@$(PROJECT_ID).iam.gserviceaccount.com \
	  --set-env-vars="GCP_PROJECT_ID=$(PROJECT_ID)" \
	  --min-instances=1 --max-instances=1 \
	  --memory=512Mi --cpu=1 \
	  --no-allow-unauthenticated

# ── Dataproc jobs ─────────────────────────────────────────────
submit-bronze: ## Submit Bronze streaming job
	bash scripts/submit_dataproc_job.sh bronze \
	  pipelines/bronze/kafka_to_gcs_prices.py

submit-silver: ## Submit Silver batch job
	bash scripts/submit_dataproc_job.sh silver \
	  pipelines/silver/gcs_to_bq_prices.py

# ── Terraform ─────────────────────────────────────────────────
tf-init: ## terraform init
	cd infra/terraform && terraform init

tf-plan: ## terraform plan
	cd infra/terraform && terraform plan \
	  -var="project_id=$(PROJECT_ID)" \
	  -var="region=$(REGION)"

tf-apply: ## terraform apply (auto-approve for CI)
	cd infra/terraform && terraform apply \
	  -var="project_id=$(PROJECT_ID)" \
	  -var="region=$(REGION)" \
	  -auto-approve