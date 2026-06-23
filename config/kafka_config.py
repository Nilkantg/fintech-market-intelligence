"""Confluent Kafka topic names and consumer group IDs."""
import os
from google.cloud import secretmanager

def _get_secret(name: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    path   = f"projects/{os.environ['GCP_PROJECT_ID']}/secrets/{name}/versions/latest"
    return client.access_secret_version(request={"name": path}).payload.data.decode()

def get_producer_config() -> dict:
    return {
        "bootstrap.servers":  _get_secret("confluent-bootstrap"),
        "security.protocol":  "SASL_SSL",
        "sasl.mechanism":     "PLAIN",
        "sasl.username":      _get_secret("confluent-api-key"),
        "sasl.password":      _get_secret("confluent-api-secret"),
        "acks":               "all",
        "retries":            5,
        "retry.backoff.ms":   500,
        "linger.ms":          10,
        "batch.size":         65536,
        "compression.type":   "snappy",
    }

def get_spark_kafka_options(topic: str, group_id: str) -> dict:
    """Returns options dict for spark.readStream.format('kafka')."""
    return {
        "kafka.bootstrap.servers":              _get_secret("confluent-bootstrap"),
        "kafka.security.protocol":              "SASL_SSL",
        "kafka.sasl.mechanism":                 "PLAIN",
        "kafka.sasl.jaas.config": (
            "org.apache.kafka.common.security.plain.PlainLoginModule required "
            f"username='{_get_secret('confluent-api-key')}' "
            f"password='{_get_secret('confluent-api-secret')}';"),
        "subscribe":                            topic,
        "startingOffsets":                      "latest",
        "failOnDataLoss":                       "false",
        "kafka.group.id":                       group_id,
    }

# Topic names
TOPIC_PRICES        = "market.prices.raw"
TOPIC_NEWS          = "market.news.raw"
TOPIC_FUNDAMENTALS  = "market.fundamentals"
TOPIC_PORTFOLIO     = "portfolio.txns"
TOPIC_DLQ           = "market.prices.dlq"

# Consumer group IDs — one per pipeline stage
GROUP_BRONZE_PRICES = "bronze-prices-consumer"
GROUP_BRONZE_NEWS   = "bronze-news-consumer"
