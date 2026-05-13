from flask import Flask, render_template, jsonify
import psycopg2, pika, json, os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/stats")
def stats():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        cur.execute("""
            SELECT
              COUNT(*) FILTER (WHERE action = 'log.login.success') as success_logins,
              COUNT(*) FILTER (WHERE action = 'log.login.failed')  as failed_logins,
              COUNT(*) FILTER (WHERE action = 'log.unauthorized_access') as unauthorized
            FROM audit_logs
        """)
        row = cur.fetchone()
        auth_stats = {"success_logins": row[0], "failed_logins": row[1], "unauthorized": row[2]}

        cur.execute("""
            SELECT action, status, ip_address, created_at
            FROM audit_logs ORDER BY created_at DESC LIMIT 20
        """)
        recent = [{"action": r[0], "status": r[1], "ip": r[2], "time": str(r[3])} for r in cur.fetchall()]

        cur.execute("""
            SELECT action, status, COUNT(*) FROM audit_logs
            WHERE action LIKE 'log.worker.%'
            GROUP BY action, status
        """)
        job_stats = [{"action": r[0], "status": r[1], "count": r[2]} for r in cur.fetchall()]

        cur.close(); conn.close()

        # Queue info
        queues = {}
        try:
            conn_mq = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            ch = conn_mq.channel()
            for q in ["worker.jobs", "logging.events", "auth.events"]:
                r = ch.queue_declare(queue=q, durable=True, passive=True)
                queues[q] = {"messages": r.method.message_count, "consumers": r.method.consumer_count}
            conn_mq.close()
        except Exception as e:
            queues = {"error": str(e)}

        return jsonify({"auth_stats": auth_stats, "recent_events": recent,
                        "job_stats": job_stats, "queues": queues})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return {"status": "healthy"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)