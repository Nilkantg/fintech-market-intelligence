"""GCP resource names — single source of truth imported by all modules."""
import os

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "fintech-market-intel")
REGION     = os.environ.get("GCP_REGION",     "us-central1")

# ── GCS ──────────────────────────────────────────────────────
BRONZE_BUCKET      = os.environ.get("BRONZE_BUCKET",      f"{PROJECT_ID}-bronze")
CHECKPOINTS_BUCKET = os.environ.get("CHECKPOINTS_BUCKET", f"{PROJECT_ID}-checkpoints")
STAGING_BUCKET     = os.environ.get("STAGING_BUCKET",     f"{PROJECT_ID}-dataproc-staging")

# ── BigQuery datasets ─────────────────────────────────────────
BQ_BRONZE = f"{PROJECT_ID}.bronze_raw"
BQ_SILVER = f"{PROJECT_ID}.silver"
BQ_GOLD   = f"{PROJECT_ID}.gold"

# ── BigQuery Silver tables ────────────────────────────────────
SILVER_PRICES       = f"{BQ_SILVER}.stg_stock_prices"
SILVER_NEWS         = f"{BQ_SILVER}.stg_news"
SILVER_FUNDAMENTALS = f"{BQ_SILVER}.stg_fundamentals"
SILVER_PORTFOLIO    = f"{BQ_SILVER}.stg_portfolio_positions"

# ── BigQuery Gold tables ──────────────────────────────────────
GOLD_DAILY_KPIS  = f"{BQ_GOLD}.daily_stock_kpis"
GOLD_SECTOR_PERF = f"{BQ_GOLD}.sector_performance"
GOLD_PORTFOLIO   = f"{BQ_GOLD}.portfolio_analytics"
GOLD_SIGNALS     = f"{BQ_GOLD}.trading_signals"

# ── Dataproc ──────────────────────────────────────────────────
DATAPROC_SA     = f"dataproc-sa@{PROJECT_ID}.iam.gserviceaccount.com"
DATAPROC_SUBNET = f"projects/{PROJECT_ID}/regions/{REGION}/subnetworks/default"