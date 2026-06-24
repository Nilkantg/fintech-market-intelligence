"""Pipeline behaviour constants — watermarks, windows, intervals."""

# ── Bronze streaming ──────────────────────────────────────────
BRONZE_PRICES_WATERMARK  = "10 minutes"
BRONZE_NEWS_WATERMARK    = "30 minutes"
BRONZE_TRIGGER_INTERVAL  = "60 seconds"
BRONZE_PARTITION_COLS    = ["dt", "hr"]

# ── Silver batch ──────────────────────────────────────────────
SILVER_LOOKBACK_HOURS      = 2
SILVER_PRICES_DEDUP_COLS   = ["ticker", "event_timestamp"]
SILVER_BQ_WRITE_METHOD     = "indirect"   # GCS → BQ load (free; avoids streaming insert cost)

# ── Gold ──────────────────────────────────────────────────────
GOLD_RUN_HOUR_UTC = 1    # 01:00 UTC = 06:30 IST

GOLD_TECHNICAL_WINDOWS = {
    "sma_short":   10,
    "sma_long":    50,
    "ema_fast":    12,
    "ema_slow":    26,
    "rsi_period":  14,
    "macd_signal":  9,
    "bb_period":   20,
    "bb_std":       2,
}