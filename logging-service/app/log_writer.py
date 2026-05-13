import psycopg2, json, logging
from app.config import DATABASE_URL
logger = logging.getLogger(__name__)

def write_audit_log(event: dict):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_logs
              (user_id, action, resource_type, resource_id, status, details, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event.get("user_id"),
            event.get("action"),
            event.get("resource_type"),
            event.get("resource_id"),
            event.get("status"),
            json.dumps(event.get("details", {})),
            event.get("ip_address"),
            event.get("user_agent")
        ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"✅ Log saved: {event.get('action')}")
    except Exception as e:
        logger.error(f"❌ DB write failed: {e}")