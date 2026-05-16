import json
import logging
import threading
import time
import pika

from app.utils.logging_client import send_log
from app.processors.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

QUEUE_NAME    = "document.events"
EXCHANGE_NAME = "document.exchange"


class DocumentConsumer(threading.Thread):
    """Background thread that processes document jobs."""

    def __init__(self, rmq_url: str, logging_service_url: str):
        super().__init__(daemon=True, name="DocumentConsumer")
        self.rmq_url = rmq_url
        self.logging_url = logging_service_url
        self._stop_event = threading.Event()
        self._connection = None

    # ------------------------------------------------------------------ #

    def run(self):
        logger.info("Worker started")
        while not self._stop_event.is_set():
            try:
                self._consume()
            except Exception as exc:
                logger.error(f"DocumentConsumer error: {exc} — restarting in 5s")
                time.sleep(5)

    def stop(self):
        self._stop_event.set()
        if self._connection and not self._connection.is_closed:
            self._connection.close()

    # ------------------------------------------------------------------ #

    def _consume(self):
        params = pika.URLParameters(self.rmq_url)
        params.heartbeat = 60
        self._connection = pika.BlockingConnection(params)
        logger.info("RabbitMQ connected")
        
        channel = self._connection.channel()

        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type="topic",
            durable=True
        )
        channel.queue_declare(
            queue=QUEUE_NAME,
            durable=True,
            arguments={"x-message-ttl": 86_400_000, "x-max-length": 5_000}
        )
        channel.queue_bind(
            queue=QUEUE_NAME,
            exchange=EXCHANGE_NAME,
            routing_key="document.*"
        )

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=QUEUE_NAME,
            on_message_callback=self._on_message
        )

        logger.info("DocumentConsumer waiting for messages")
        channel.start_consuming()

    def _on_message(self, channel, method, properties, body: bytes):
        routing_key = method.routing_key
        try:
            event = json.loads(body)
            if routing_key == "document.uploaded":
                logger.info("document.uploaded received")
            else:
                logger.info(f"Received [{routing_key}]: {event}")
            
            self._process(routing_key, event)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except json.JSONDecodeError:
            logger.error(f"Non-JSON message: {body[:200]}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as exc:
            logger.exception(f"Error processing [{routing_key}]: {exc}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    # ------------------------------------------------------------------ #

    def _process(self, routing_key: str, event: dict):
        handlers = {
            "document.uploaded":      self._handle_upload,
            "document.downloaded":    self._handle_download,
            "document.ai_query":      self._handle_ai_query,
            "document.chunk_request": self._handle_chunking,
        }
        handler = handlers.get(routing_key)
        if handler:
            handler(event)
        else:
            logger.warning(f"No handler for routing key: {routing_key}")

    # ─── Handlers ──────────────────────────────────────────────────────

    def _handle_upload(self, event: dict):
        """Log the upload and fire off a chunking job."""
        send_log(self.logging_url, {
            "source":   "worker-service",
            "action":   "uploads",
            "user_id":  event.get("user_id"),
            "details":  event,
            "status":   "success",
        })
        # logger.info(f"Upload logged for document_id: {event.get('document_id')}")

        # Trigger real chunking
        self._run_chunking_job(event)

    def _handle_download(self, event: dict):
        send_log(self.logging_url, {
            "source":  "worker-service",
            "action":  "downloads",
            "user_id": event.get("user_id"),
            "details": event,
            "status":  "success",
        })

    def _handle_ai_query(self, event: dict):
        send_log(self.logging_url, {
            "source":  "worker-service",
            "action":  "ai_queries",
            "user_id": event.get("user_id"),
            "details": event,
            "status":  "success",
        })

    def _handle_chunking(self, event: dict):
        """Background job: chunk document text and generate embeddings."""
        self._run_chunking_job(event)

    # ─── Core chunking logic ─────────────────────────────────

    def _run_chunking_job(self, event: dict):
        doc_id   = event.get("document_id")
        if not doc_id:
            logger.error("No document_id provided in event")
            return

        # logger.info(f"[RAG Pipeline] Starting processing for document: {doc_id}")

        send_log(self.logging_url, {
            "source":  "worker-service",
            "action":  "worker_status",
            "details": {"job": "processing_started", "document_id": doc_id},
            "status":  "info",
        })

        try:
            # Process document (Decrypt -> Extract -> Chunk -> Save)
            DocumentProcessor.process_document(doc_id)
            logger.info("processing completed")

            send_log(self.logging_url, {
                "source":  "worker-service",
                "action":  "background_job_status",
                "details": {
                    "job":          "processing_complete",
                    "document_id":  doc_id,
                    "status":       "success",
                },
                "status": "success",
            })

        except Exception as exc:
            logger.error(f"[RAG Pipeline] Failed for {doc_id}: {exc}")
            send_log(self.logging_url, {
                "source":  "worker-service",
                "action":  "background_job_status",
                "details": {
                    "job":         "processing_failed",
                    "document_id": doc_id,
                    "error":       str(exc),
                },
                "status": "failed",
            })
