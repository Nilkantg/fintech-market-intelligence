# Real-Time Financial Market Intelligence Platform
> End-to-end streaming data platform on GCP — built for a 1–2 YOE Data Engineer portfolio

## Stack
| Layer | Service | Cost |
|---|---|---|
| Streaming broker | Confluent Cloud Kafka | Free (5 GB/mo) |
| Producers | Cloud Run (containerised Python) | Free tier |
| Bronze processing | Dataproc Serverless PySpark | ~$5–15/mo |
| Silver/Gold storage | BigQuery | Free (10 GB + 1 TB queries/mo) |
| Raw landing | GCS Standard | Free (5 GB always-free) |
| Orchestration | Airflow on GCE e2-micro | Free (always-free tier) |
| Scheduling | Cloud Scheduler | Free (3 jobs/mo) |
| Governance | Dataplex | Free (metadata scan) |
| Data quality | Great Expectations + Dataplex DQ | Free (open-source) |
| Analytics | Looker Studio | Free |
| CI/CD | GitHub Actions | Free (2000 min/mo) |
| Container registry | Artifact Registry | Free (0.5 GB) |
| Monitoring | Cloud Monitoring + Logging | Free (50 GB logs/mo) |

**Estimated monthly cost on free trial: ~$10–20/mo**

## Architecture
```
Finnhub / Alpha Vantage / Yahoo Finance
        ↓
Cloud Run Producers  →  Confluent Kafka topics
        ↓
Dataproc Serverless (Bronze job)  →  GCS Bronze (Parquet, partitioned)
        ↓
Dataproc Serverless (Silver job)  →  BigQuery Silver (cleaned, deduplicated)
        ↓
BigQuery SQL Scheduled Queries (Gold)  →  BigQuery Gold (KPIs, signals)
        ↓
Looker Studio dashboards
```

## Build sequence
1. GCP project + IAM (`scripts/setup_gcp.sh`)
2. GCS buckets + BigQuery datasets (Terraform or gcloud)
3. Confluent Kafka cluster + topics (`scripts/setup_kafka_topics.sh`)
4. Price producer → Cloud Run (`producers/price_producer/`)
5. Bronze streaming job (`pipelines/bronze/kafka_to_gcs_prices.py`)
6. Silver batch job (`pipelines/silver/gcs_to_bq_prices.py`)
7. Gold SQL aggregations (`sql/gold/`)
8. Airflow on e2-micro + DAGs (`scripts/setup_airflow_vm.sh`, `dags/`)
9. Great Expectations DQ (`dq/`)
10. Looker Studio dashboard
11. GitHub Actions CI/CD (`.github/workflows/`)
