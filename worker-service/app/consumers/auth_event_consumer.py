"""
Auth Event Consumer
Listens to auth.events queue and forwards structured audit logs
to the Logging Service.

Routing keys consumed:
  auth.login.success
  auth.login.failed
  auth.logout
  auth.register
  auth.unauthorized
"""
import json
import logging
import threading
import time

import pika

from app.utils.logging_client import send_log

logger = logging.getLogger(__name__)

QUEUE_NAME    = "auth.events"
EXCHANGE_NAME = "auth.exchange"


class AuthEventConsumer(threading.Thread):
    """Background thread that consumes auth events from RabbitMQ."""

    def __init__(self, rmq_conn, logging_service_url: str):
        super().__init__(daemon=True, name="AuthEventConsumer")
        self.rmq = rmq_conn
        self.logging_url = logging_service_url
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------ #
    #  Thread entry                                                        #
    # ------------------------------------------------------------------ #

    def run(self):
        while not self._stop_event.is_set():
            try:
                self._consume()
            except Exception as exc:
                logger.error(f"AuthEventConsumer error: {exc} — restarting in 5s")
                time.sleep(5)

    def stop(self):
        self._stop_event.set()

    # ------------------------------------------------------------------ #
    #  Consumer logic                                                       #
    # ------------------------------------------------------------------ #

    def _consume(self):
        channel = self.rmq.channel()

        # Declare exchange & queue (idempotent)
        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type="topic",
            durable=True
        )
        channel.queue_declare(
            queue=QUEUE_NAME,
            durable=True,
            arguments={"x-message-ttl": 86_400_000, "x-max-length": 10_000}
        )
        channel.queue_bind(
            queue=QUEUE_NAME,
            exchange=EXCHANGE_NAME,
            routing_key="auth.*"
        )

        channel.basic_qos(prefetch_count=10)
        channel.basic_consume(
            queue=QUEUE_NAME,
            on_message_callback=self._on_message
        )

        logger.info(f"AuthEventConsumer listening on queue '{QUEUE_NAME}' …")
        channel.start_consuming()

    def _on_message(self, channel, method, properties, body: bytes):
        routing_key = method.routing_key
        try:
            event = json.loads(body)
            logger.info(f"Received [{routing_key}]: {event}")
            self._process(routing_key, event)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except json.JSONDecodeError:
            logger.error(f"Non-JSON message on {routing_key}: {body[:200]}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as exc:
            logger.exception(f"Error processing [{routing_key}]: {exc}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    # ------------------------------------------------------------------ #
    #  Processing                                                          #
    # ------------------------------------------------------------------ #

    def _process(self, routing_key: str, event: dict):
        action_map = {
            "auth.login.success": "successful_login",
            "auth.login.failed":  "failed_login",
            "auth.logout":        "logout",
            "auth.register":      "user_registered",
            "auth.unauthorized":  "unauthorized_access",
        }

        action = action_map.get(routing_key, routing_key)

        payload = {
            "source":     "worker-service",
            "action":     action,
            "user_id":    event.get("user_id"),
            "user_email": event.get("email"),
            "ip_address": event.get("ip_address"),
            "user_agent": event.get("user_agent"),
            "details":    event,
            "status":     "success" if "success" in routing_key or "logout" in routing_key or "register" in routing_key else "failed",
        }

        success = send_log(self.logging_url, payload)
        if success:
            logger.info(f"Event [{action}] forwarded to logging service ✓")
        else:
            logger.warning(f"Event [{action}] NOT logged (logging service unavailable)")
