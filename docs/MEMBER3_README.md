# Member 3 — Queue, Worker & Logging Services

## Overview

This adds three deliverables on top of the existing Auth + FAQ + Nginx stack:

| Service | Container | Port |
|---------|-----------|------|
| **Worker Service** | `worker_service` | — (no HTTP, RabbitMQ consumer) |
| **Logging Service** | `logging_service` | `5002` (internal) |
| **Monitoring Dashboard** | `monitoring_dashboard` | `8080` (public) |

---

## Architecture

```
Auth Service  ──publishes──►  auth.exchange  (RabbitMQ topic)
                                    │
                              auth.events queue
                                    │
FAQ Service   ──publishes──►  document.exchange
                                    │
                            document.events queue
                                    │
                           Worker Service (consumer)
                                    │
                        ┌───────────┴───────────┐
                        │                       │
                  Auth Events             Document Jobs
                  (login/logout)          (upload/chunk/embed)
                        │                       │
                        └───────────┬───────────┘
                                    │  HTTP POST /internal/logs
                             Logging Service
                                    │
                               PostgreSQL
                             (service_logs)
                                    │
                          Monitoring Dashboard
                           (reads /api/logs)
```

---

## How to Run

### 1. Start everything

```bash
cd ai-university-faq-assistant
docker compose up --build -d
```

Wait ~30 seconds for all services to be healthy, then check:

```bash
docker compose ps
```

All containers should show `healthy` or `running`.

### 2. Open the Monitoring Dashboard

```
http://localhost:8080
```

The dashboard auto-refreshes every 30 seconds. You can:
- View all audit log entries in real time
- See KPI counters (logins, uploads, AI queries, unauthorized access)
- Check worker job status (chunking, embeddings)
- Publish test events directly from the UI

### 3. Trigger real events

Register a user:
```bash
curl -X POST http://localhost/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@uni.edu","password":"Test1234!"}'
```

Login:
```bash
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@uni.edu","password":"Test1234!"}'
```

Failed login (wrong password):
```bash
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@uni.edu","password":"wrongpassword"}'
```

Each action publishes to RabbitMQ → Worker consumes → Logging Service stores → Dashboard shows.

---

## Service Details

### Worker Service (`worker-service/`)

- **`app/consumers/auth_event_consumer.py`** — consumes `auth.events` queue
  - Handles: `auth.login.success`, `auth.login.failed`, `auth.logout`, `auth.register`, `auth.unauthorized`
  - Forwards structured logs to Logging Service via HTTP

- **`app/consumers/document_consumer.py`** — consumes `document.events` queue
  - Handles: `document.uploaded`, `document.downloaded`, `document.ai_query`, `document.chunk_request`
  - Runs document chunking (overlapping 500-word windows) + embedding generation (SHA-256 demo)
  - Reports job status back to Logging Service

- **`app/utils/rabbitmq.py`** — thread-safe connection with auto-reconnect
- **`app/utils/logging_client.py`** — HTTP client for the Logging Service

### Logging Service (`logging-service/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/internal/logs` | POST | Write a log entry (used by Worker, Auth) |
| `/api/logs` | GET | Paginated log listing — filters: `action`, `source`, `status`, `since` |
| `/api/logs/stats` | GET | Aggregate counts per action — param: `hours` (default 24) |
| `/api/logs/worker-status` | GET | Latest worker/job log entries |
| `/health` | GET | Health check |

Actions logged:
- `successful_login` / `failed_login` / `logout` / `user_registered`
- `uploads` / `downloads` / `ai_queries`
- `unauthorized_access`
- `worker_status` / `background_job_status`

### Monitoring Dashboard (`monitoring-dashboard/`)

Single-page HTML/JS app served by Nginx. Features:
- **KPI cards** — 8 counters updated from `/api/logs/stats`
- **Audit log table** — last 30 entries with action, source, user, IP, status
- **Bar chart** — events breakdown by action
- **Worker jobs panel** — processed / failed background jobs
- **RabbitMQ queues info** — static view of configured queues/exchanges
- **Queue test tool** — publish any event type directly from the browser
- Configurable logging service URL and auto-refresh interval

---

## Publishing Document Events from FAQ Service

The FAQ Service can publish document events by adding this to its code:

```python
import pika, json, os

def publish_document_event(routing_key: str, payload: dict):
    url = os.getenv("RABBITMQ_URL", "amqp://admin:password@rabbitmq:5672/")
    conn = pika.BlockingConnection(pika.URLParameters(url))
    ch   = conn.channel()
    ch.exchange_declare(exchange="document.exchange", exchange_type="topic", durable=True)
    ch.basic_publish(
        exchange="document.exchange",
        routing_key=routing_key,
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    conn.close()

# Example — when a document is uploaded:
publish_document_event("document.uploaded", {
    "user_id":     42,
    "filename":    "lecture_notes.pdf",
    "document_id": "doc_001",
    "text":        "Full extracted text goes here…",
})
```

---

## Logs & Debugging

```bash
# Worker logs
docker compose logs -f worker-service

# Logging service logs
docker compose logs -f logging-service

# Check stored logs via API
curl http://localhost:8080/api/logs | python3 -m json.tool

# Check stats
curl "http://localhost:8080/api/logs/stats?hours=1" | python3 -m json.tool

# RabbitMQ management UI (via Nginx proxy)
# Check docs/INFRASTRUCTURE.md for the admin credentials and URL
```

---

## File Structure

```
ai-university-faq-assistant/
├── worker-service/
│   ├── Dockerfile
│   ├── requirements.txt          # pika, requests
│   ├── main.py                   # entry point
│   └── app/
│       ├── consumers/
│       │   ├── auth_event_consumer.py
│       │   └── document_consumer.py
│       └── utils/
│           ├── rabbitmq.py
│           └── logging_client.py
│
├── logging-service/
│   ├── Dockerfile
│   ├── requirements.txt          # Flask, SQLAlchemy, gunicorn
│   ├── main.py
│   └── app/
│       ├── __init__.py           # app factory
│       ├── models/log_entry.py   # service_logs table
│       └── routes/
│           ├── log_routes.py     # write + read endpoints
│           └── health_routes.py
│
├── monitoring-dashboard/
│   ├── Dockerfile                # nginx:alpine
│   ├── nginx.conf                # proxy to logging-service
│   └── index.html                # full SPA dashboard
│
├── migrations/
│   ├── 001_initial_schema.sql    # existing
│   └── 002_service_logs.sql      # NEW — service_logs table
│
├── app/services/
│   └── event_publisher.py        # NEW — RabbitMQ publisher for auth service
│
├── rabbitmq/
│   └── definitions.json          # UPDATED — added document.exchange + queue
│
├── requirements.txt              # UPDATED — added pika==1.3.2
└── docker-compose.yml            # UPDATED — added 3 new services
```
