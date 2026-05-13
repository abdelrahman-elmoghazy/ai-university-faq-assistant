"""
Worker Service — Main Entry Point
Consumes messages from RabbitMQ and processes background jobs
"""
import os
import sys
import signal
import logging
import time

from app.consumers.auth_event_consumer import AuthEventConsumer
from app.consumers.document_consumer import DocumentConsumer
from app.utils.rabbitmq import RabbitMQConnection

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("worker")

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    f"amqp://{os.getenv('RABBITMQ_USER','admin')}:{os.getenv('RABBITMQ_PASSWORD','password')}@rabbitmq:5672/"
)
LOGGING_SERVICE_URL = os.getenv("LOGGING_SERVICE_URL", "http://logging-service:5002")


def shutdown(signum, frame):
    logger.info("Shutdown signal received — stopping workers …")
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    logger.info("Worker Service starting …")

    # Wait for RabbitMQ to be ready
    rmq = RabbitMQConnection(RABBITMQ_URL)
    for attempt in range(1, 11):
        if rmq.connect():
            logger.info("Connected to RabbitMQ")
            break
        logger.warning(f"RabbitMQ not ready (attempt {attempt}/10) — retrying in 5s")
        time.sleep(5)
    else:
        logger.error("Could not connect to RabbitMQ after 10 attempts — exiting")
        sys.exit(1)

    # Start consumers
    auth_consumer   = AuthEventConsumer(rmq, LOGGING_SERVICE_URL)
    doc_consumer    = DocumentConsumer(rmq, LOGGING_SERVICE_URL)

    auth_consumer.start()
    doc_consumer.start()

    logger.info("All consumers started — waiting for messages …")

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        auth_consumer.stop()
        doc_consumer.stop()
        rmq.close()
        logger.info("Worker Service stopped")


if __name__ == "__main__":
    main()
