"""
RabbitMQ Publisher — Auth Service
Publishes audit events to auth.exchange so the Worker Service can consume them.

Usage:
    from app.services.event_publisher import publish_auth_event
    publish_auth_event("auth.login.success", {"user_id": 1, "email": "a@b.com"})
"""
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
EXCHANGE_NAME = "auth.exchange"


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


def publish_auth_event(routing_key: str, payload: dict) -> bool:
    """
    Publish a JSON payload to auth.exchange with the given routing key.
    Silently swallows errors so the auth service never fails due to MQ issues.
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
            logger.debug(f"Published [{routing_key}]: {payload}")
            return True
        except Exception as exc:
            logger.warning(f"Failed to publish event [{routing_key}]: {exc}")
            _connection = None          # force reconnect next time
            return False
