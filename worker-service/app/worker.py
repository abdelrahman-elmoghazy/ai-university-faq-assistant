import pika, json, logging, time
from app.config import RABBITMQ_URL, WORKER_QUEUE
from app.tasks.document_tasks import process_document
from app.tasks.embedding_tasks import generate_embedding

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [WORKER] %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

TASK_HANDLERS = {
    "document.chunk": process_document,
    "embedding.generate": generate_embedding,
}

def on_message(channel, method, properties, body):
    try:
        payload = json.loads(body)
        task_type = payload.get("task_type")
        logger.info(f"Received task: {task_type}")
        handler = TASK_HANDLERS.get(task_type)
        if not handler:
            logger.warning(f"Unknown task: {task_type}")
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return
        result = handler(payload)
        logger.info(f"Done: {result}")
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Task failed: {e}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def start_worker():
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()
            channel.queue_declare(queue=WORKER_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=WORKER_QUEUE, on_message_callback=on_message)
            logger.info(f"Worker ready ✅ listening on: {WORKER_QUEUE}")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            logger.error("RabbitMQ not ready, retrying in 5s...")
            time.sleep(5)