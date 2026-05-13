"""
Document Consumer
Listens to document.events queue and handles:
  - document.uploaded      → log upload + trigger chunking job
  - document.downloaded    → log download
  - document.ai_query      → log AI query
  - document.chunk_request → run document chunking + embedding simulation

These jobs are published by the FAQ Service or the Auth Service.
"""
import json
import logging
import threading
import time
import hashlib

import pika

from app.utils.logging_client import send_log

logger = logging.getLogger(__name__)

QUEUE_NAME    = "document.events"
EXCHANGE_NAME = "document.exchange"


class DocumentConsumer(threading.Thread):
    """Background thread that processes document jobs."""

    def __init__(self, rmq_conn, logging_service_url: str):
        super().__init__(daemon=True, name="DocumentConsumer")
        self.rmq = rmq_conn
        self.logging_url = logging_service_url
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------ #

    def run(self):
        while not self._stop_event.is_set():
            try:
                self._consume()
            except Exception as exc:
                logger.error(f"DocumentConsumer error: {exc} — restarting in 5s")
                time.sleep(5)

    def stop(self):
        self._stop_event.set()

    # ------------------------------------------------------------------ #

    def _consume(self):
        channel = self.rmq.channel()

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

        channel.basic_qos(prefetch_count=5)
        channel.basic_consume(
            queue=QUEUE_NAME,
            on_message_callback=self._on_message
        )

        logger.info(f"DocumentConsumer listening on queue '{QUEUE_NAME}' …")
        channel.start_consuming()

    def _on_message(self, channel, method, properties, body: bytes):
        routing_key = method.routing_key
        try:
            event = json.loads(body)
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
        logger.info(f"Upload logged for file: {event.get('filename')}")

        # Simulate triggering chunking
        self._run_chunking_job(event)

    def _handle_download(self, event: dict):
        send_log(self.logging_url, {
            "source":  "worker-service",
            "action":  "downloads",
            "user_id": event.get("user_id"),
            "details": event,
            "status":  "success",
        })
        logger.info(f"Download logged for file: {event.get('filename')}")

    def _handle_ai_query(self, event: dict):
        send_log(self.logging_url, {
            "source":  "worker-service",
            "action":  "ai_queries",
            "user_id": event.get("user_id"),
            "details": event,
            "status":  "success",
        })
        logger.info(f"AI query logged: {str(event.get('query',''))[:80]}")

    def _handle_chunking(self, event: dict):
        """Background job: chunk document text and generate embeddings."""
        self._run_chunking_job(event)

    # ─── Core chunking/embedding logic ─────────────────────────────────

    def _run_chunking_job(self, event: dict):
        doc_id   = event.get("document_id", "unknown")
        text     = event.get("text", "")
        filename = event.get("filename", "unknown")

        logger.info(f"[Chunking] Starting job for document: {doc_id} ({filename})")

        send_log(self.logging_url, {
            "source":  "worker-service",
            "action":  "worker_status",
            "details": {"job": "chunking_started", "document_id": doc_id, "filename": filename},
            "status":  "info",
        })

        try:
            chunks = self._chunk_text(text)
            embeddings = [self._fake_embedding(c) for c in chunks]

            logger.info(
                f"[Chunking] Done for {doc_id}: {len(chunks)} chunks, "
                f"{len(embeddings)} embeddings generated"
            )

            send_log(self.logging_url, {
                "source":  "worker-service",
                "action":  "background_job_status",
                "details": {
                    "job":          "chunking_complete",
                    "document_id":  doc_id,
                    "chunks":       len(chunks),
                    "embeddings":   len(embeddings),
                    "status":       "success",
                },
                "status": "success",
            })

        except Exception as exc:
            logger.error(f"[Chunking] Failed for {doc_id}: {exc}")
            send_log(self.logging_url, {
                "source":  "worker-service",
                "action":  "background_job_status",
                "details": {
                    "job":         "chunking_failed",
                    "document_id": doc_id,
                    "error":       str(exc),
                },
                "status": "failed",
            })

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []
        words  = text.split()
        chunks = []
        start  = 0
        while start < len(words):
            end = start + chunk_size
            chunks.append(" ".join(words[start:end]))
            start += chunk_size - overlap
        return chunks

    @staticmethod
    def _fake_embedding(text: str) -> str:
        """Simulate an embedding vector (deterministic hash for demo)."""
        return hashlib.sha256(text.encode()).hexdigest()
