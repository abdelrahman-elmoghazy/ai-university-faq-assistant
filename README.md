# AI University FAQ Assistant

A distributed system for handling university FAQ queries with AI-powered responses. Built as a course project for Secure Distributed Systems. The system uses a microservices architecture with JWT authentication, message queues, encrypted file storage, and a centralized monitoring pipeline.

## Architecture

9 containers orchestrated with Docker Compose:

| Service | Container | Description |
|---------|-----------|-------------|
| API Gateway | `api_gateway` (Nginx) | Reverse proxy, HTTPS termination, rate limiting, security headers |
| Auth Service | `auth_service` | Registration, login, JWT tokens, RBAC |
| FAQ Service | `faq_service` | Question answering, AI integration, file uploads |
| Worker Service | `worker_service` | Background document processing via RabbitMQ |
| Logging Service | `logging_service` | Centralized audit trail storage |
| Monitoring Dashboard | `monitoring_dashboard` | Real-time system monitoring UI |
| Frontend | `frontend` | React SPA (login, chat, file upload, admin panel) |
| PostgreSQL | `postgres_db` | Main database (with pgvector extension) |
| RabbitMQ | `rabbitmq` | Message broker for async tasks |

Network layout:
- `public_net` — only Nginx is exposed to the host (ports 80, 443)
- `internal_net` (`internal: true`) — all backend services, no direct public access

## Security Features

- JWT authentication with access + refresh tokens (HS256, configurable expiration)
- Password hashing with bcrypt (12 rounds)
- Role-based access control — `admin` and `user` roles with a permissions table
- OAuth2 login support (Google, GitHub)
- HTTPS with TLS, automatic HTTP-to-HTTPS redirect
- Rate limiting per endpoint (login: 5/min, auth: 10/min, general API: 30/min)
- Input validation on all endpoints (email format, password strength, question length, file size)
- Secure file upload — extension + MIME type validation, blocked dangerous types (.exe, .php, .js, .bat, .sh)
- File encryption at rest using Fernet (AES-128-CBC + HMAC-SHA256)
- SHA-256 integrity verification for uploaded files
- Service-to-service authentication using internal API keys
- Nginx strips `X-Internal-API-Key` from external requests to prevent spoofing
- Security headers on all responses (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
- Error handling hides stack traces in production mode

## How to Run

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env and fill in all CHANGE_ME values

# 2. Generate SSL certs (self-signed for development)
bash scripts/generate_certs.sh localhost

# 3. Start everything
docker compose up --build

# 4. Wait ~30s for all services to initialize, then verify
docker compose ps
```

Access points:
- Frontend: http://localhost:3000
- API (HTTPS): https://localhost
- Monitoring Dashboard: http://localhost:8081

## API Endpoints

| Service | Base Path | Key Endpoints |
|---------|-----------|---------------|
| Auth | `/api/auth` | `/register`, `/login`, `/refresh`, `/me`, `/logout` |
| FAQ | `/api/faq` | `/ask`, `/history`, `/conversations` |
| Files | `/api/files` | `/upload`, `/my-files`, `/<id>/verify` |
| Admin | `/api/admin` | `/stats`, `/audit-logs`, `/recent-queries` |
| Logging | `/internal` | `/logs` (internal only, not accessible from outside) |

All protected endpoints require `Authorization: Bearer <token>` header.
Admin endpoints additionally require the `admin` role in the JWT payload.

## Database

PostgreSQL 15 with the following tables:

- `users` — accounts with hashed passwords
- `roles`, `permissions`, `user_roles` — RBAC infrastructure
- `documents` — uploaded file metadata, encrypted paths, SHA-256 hashes
- `chunks` — document segments for RAG processing
- `questions`, `answers` — AI chat history
- `audit_logs` — system event tracking
- `service_logs` — worker and service-level logs

Migrations are in `migrations/` and run automatically on first startup.

## Message Queue

```
Auth/FAQ Service  →  publishes event  →  RabbitMQ (topic exchange)
                                              ↓
                                      Worker Service (consumer)
                                              ↓
                                      Logging Service (HTTP POST)
                                              ↓
                                         PostgreSQL
                                              ↓
                                     Monitoring Dashboard
```

Events tracked: login success/failure, logout, registration, file uploads, AI queries, worker job status.

RabbitMQ is configured with a custom user (no default guest account), credentials set via `.env`.

## Testing

```bash
# Infrastructure tests (HTTPS, rate limiting, headers, port exposure)
bash scripts/test_infra.sh

# API integration tests
python test_api.py

# Unit tests
python -m pytest tests/
```

## Project Structure

```
├── app/                    # Auth Service (Flask)
│   ├── middleware/          #   JWT validation middleware
│   ├── models/             #   SQLAlchemy models
│   ├── routes/             #   Auth and admin endpoints
│   ├── services/           #   Auth, RBAC, OAuth, event publishing
│   └── schemas/            #   Input validation schemas
├── faq-service/            # FAQ Service (Flask)
│   └── app/                #   Controllers, routes, services, validators
├── worker-service/         # Background worker (RabbitMQ consumer)
│   └── app/                #   Consumers, processors, tasks
├── logging-service/        # Audit log service (Flask)
│   └── app/                #   Log routes, models, services
├── monitoring-dashboard/   # Dashboard SPA (static HTML/JS)
├── frontend/               # React + Vite frontend
│   └── src/                #   Pages, components, API layer, auth context
├── nginx/                  # API Gateway configuration
│   ├── conf.d/             #   HTTPS, redirect, RabbitMQ proxy configs
│   └── certs/              #   SSL certificates
├── rabbitmq/               # RabbitMQ config and queue definitions
├── migrations/             # SQL schema files
├── scripts/                # Helper scripts (certs, tests, management)
├── tests/                  # Test files
├── config/                 # App configuration
├── docker-compose.yml      # Full stack orchestration
└── .env.example            # Environment variable template
```
