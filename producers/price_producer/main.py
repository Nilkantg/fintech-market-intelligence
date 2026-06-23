import os
import json
import time
import signal
import structlog
import finnhub
from confluent_kafka import Producer, KafkaException
from google.cloud import secretmanager
from datetime import datetime, timezone

log = structlog.get_logger()

# ── Secret fetching ──────────────────────────────────────────
def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ["GCP_PROJECT_ID"]
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# ── Kafka delivery report ─────────────────────────────────────
def delivery_report(err, msg):
    if err is not None:
        log.error("delivery_failed", error=str(err), topic=msg.topic())
    else:
        log.debug("delivered", topic=msg.topic(), partition=msg.partition(), offset=msg.offset())

# ── Kafka producer setup ──────────────────────────────────────
def create_producer() -> Producer:
    bootstrap = get_secret("confluent-bootstrap")
    api_key   = get_secret("confluent-api-key")
    api_secret = get_secret("confluent-api-secret")
    
    return Producer({
        "bootstrap.servers": bootstrap,
        "security.protocol": "SASL_SSL",
        "sasl.mechanism":    "PLAIN",
        "sasl.username":     api_key,
        "sasl.password":     api_secret,
        # Reliability settings for production-grade producer
        "acks":              "all",          # wait for all in-sync replicas
        "retries":           5,
        "retry.backoff.ms":  500,
        "linger.ms":         10,             # batch for 10ms before sending
        "batch.size":        65536,          # 64KB batch
        "compression.type":  "snappy",       # compress batches
    })

# ── Finnhub quote polling ──────────────────────────────────────
TICKERS = [
    # Nifty50 components — relevant for Indian market focus
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS",
    # US large caps for breadth
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "JPM", "V", "JNJ",
]

def build_price_event(ticker: str, quote: dict) -> dict:
    """Normalise Finnhub quote response into a clean event schema."""
    return {
        "event_type":       "price_tick",
        "ticker":           ticker,
        "current_price":    quote.get("c"),      # current price
        "change":           quote.get("d"),      # change
        "pct_change":       quote.get("dp"),     # % change
        "high":             quote.get("h"),      # day high
        "low":              quote.get("l"),      # day low
        "open":             quote.get("o"),      # open
        "prev_close":       quote.get("pc"),     # previous close
        "event_timestamp":  datetime.now(timezone.utc).isoformat(),
        "source":           "finnhub",
        "schema_version":   "1.0",
    }

def main():
    log.info("producer_starting")
    producer = create_producer()
    finnhub_client = finnhub.Client(api_key=os.environ["FINNHUB_API_KEY"])
    
    # Graceful shutdown on SIGTERM (Cloud Run sends this before scaling to zero)
    shutdown = False
    def handle_sigterm(signum, frame):
        nonlocal shutdown
        log.info("sigterm_received_flushing")
        shutdown = True
    signal.signal(signal.SIGTERM, handle_sigterm)
    
    while not shutdown:
        for ticker in TICKERS:
            try:
                quote = finnhub_client.quote(ticker)
                
                # Skip stale quotes (Finnhub free tier returns zeros for market-closed)
                if quote.get("c", 0) == 0:
                    log.debug("skipping_zero_quote", ticker=ticker)
                    continue
                
                event = build_price_event(ticker, quote)
                
                producer.produce(
                    topic="market.prices.raw",
                    key=ticker.encode("utf-8"),
                    value=json.dumps(event).encode("utf-8"),
                    on_delivery=delivery_report,
                )
                
            except Exception as e:
                # Publish to dead letter queue — never crash the producer loop
                log.error("quote_fetch_failed", ticker=ticker, error=str(e))
                producer.produce(
                    topic="market.prices.dlq",
                    key=ticker.encode("utf-8"),
                    value=json.dumps({"ticker": ticker, "error": str(e),
                                      "ts": datetime.now(timezone.utc).isoformat()}).encode(),
                )
        
        # Flush after each full sweep
        producer.poll(0)
        producer.flush(timeout=10)
        
        log.info("sweep_complete", tickers_processed=len(TICKERS))
        time.sleep(60)  # Finnhub free tier: 60 calls/min limit
    
    producer.flush(timeout=30)
    log.info("producer_shutdown_clean")

if __name__ == "__main__":
    main()