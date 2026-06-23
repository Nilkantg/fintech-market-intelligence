"""Pipeline behaviour config — watermarks, intervals, partition columns."""

# Bronze streaming
BRONZE_PRICES_WATERMARK     = "10 minutes"
BRONZE_NEWS_WATERMARK        = "30 minutes"
BRONZE_TRIGGER_INTERVAL      = "60 seconds"   # micro-batch interval
BRONZE_PARTITION_COLS        = ["dt", "hr"]    # partition cols written to GCS

# Silver batch
SILVER_LOOKBACK_HOURS        = 2              # how many GCS partitions to process per run
SILVER_PRICES_DEDUP_COLS     = ["ticker", "event_timestamp"]
SILVER_BQ_WRITE_METHOD       = "indirect"     # GCS staging → BQ load (free vs streaming insert)

# Gold
GOLD_RUN_HOUR_IST            = 6             # daily Gold job at 06:30 IST
GOLD_TECHNICAL_WINDOWS       = {
    "sma_short":  10,
    "sma_long":   50,
    "ema_fast":   12,
    "ema_slow":   26,
    "rsi_period": 14,
    "macd_signal": 9,
}
