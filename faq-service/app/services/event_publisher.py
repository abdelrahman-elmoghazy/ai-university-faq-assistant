import json
import logging
import os
import threading
import pika

logger = logging.getLogger(__name__)

_connection = None
_channel    = None
_lock       = threading.Lock()

RABBITMQ_URL  = os.getenv(
    "RABBITMQ_URL",
    f"amqp://{os.getenv('RABBITMQ_USER','admin')}:{os.getenv('RABBITMQ_PASSWORD','password')}@rabbitmq:5672/"
)
EXCHANGE_NAME = "document.exchange"

def _get_channel():
    global _connection, _channel
    try:
        if _connection and not _connection.is_closed and _channel and _channel.is_open:
            return _channel
        params = pika.URLParameters(RABBITMQ_URL)
        params.heartbeat = 60
        _connection = pika.BlockingConnection(params)
        _channel    = _connection.channel()
        _channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type="topic",
            durable=True
        )
        return _channel
    except Exception as exc:
        logger.warning(f"RabbitMQ unavailable — event will not be published: {exc}")
        return None

def publish_document_event(routing_key: str, payload: dict) -> bool:
    """
    Publish a JSON payload to document.exchange with the given routing key.
    """
    with _lock:
        try:
            channel = _get_channel()
            if channel is None:
                return False
            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=routing_key,
                body=json.dumps(payload),
                properties=pika.BasicProperties(
                    delivery_mode=2,        # persistent
                    content_type="application/json"
                )
            )
            logger.info(f"Published [{routing_key}]: {payload}")
            return True
        except Exception as exc:
            logger.warning(f"Failed to publish event [{routing_key}]: {exc}")
            _connection = None          # force reconnect next time
            return False
