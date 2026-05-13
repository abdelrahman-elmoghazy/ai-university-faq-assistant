import pika, json, logging, time
from app.config import RABBITMQ_URL, LOGGING_QUEUE
from app.log_writer import write_audit_log

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [LOGGING] %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def on_log_event(channel, method, properties, body):
    try:
        event = json.loads(body)
        write_audit_log(event)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error: {e}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_consumer():
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()
            channel.queue_declare(queue=LOGGING_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=10)
            channel.basic_consume(queue=LOGGING_QUEUE, on_message_callback=on_log_event)
            logger.info(f"Logging service ready ✅ listening on: {LOGGING_QUEUE}")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            logger.error("RabbitMQ not ready, retrying in 5s...")
            time.sleep(5)