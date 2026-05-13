"""
RabbitMQ connection helper — handles reconnect logic
"""
import logging
import threading
import pika

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """Thread-safe RabbitMQ connection wrapper with auto-reconnect."""

    def __init__(self, url: str):
        self.url = url
        self._connection = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        try:
            params = pika.URLParameters(self.url)
            params.heartbeat = 60
            params.blocked_connection_timeout = 300
            self._connection = pika.BlockingConnection(params)
            return True
        except Exception as exc:
            logger.error(f"RabbitMQ connect error: {exc}")
            self._connection = None
            return False

    def channel(self):
        with self._lock:
            if not self._connection or self._connection.is_closed:
                self.connect()
            return self._connection.channel()

    def close(self):
        if self._connection and not self._connection.is_closed:
            self._connection.close()
