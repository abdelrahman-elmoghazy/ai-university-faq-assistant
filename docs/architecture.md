# Architecture Overview

## System Diagram

```
                        Internet
                           │
                    ┌──────┴──────┐
                    │  Nginx      │  (ports 80, 443)
                    │  API Gateway│  HTTPS, rate limiting,
                    │             │  security headers
                    └──────┬──────┘
                           │
              ┌────────────┼────────────────┐
              │            │                │
         ┌────┴────┐  ┌────┴────┐    ┌──────┴──────┐
         │  Auth   │  │   FAQ   │    │   Logging   │
         │ Service │  │ Service │    │   Service   │
         │ :5000   │  │ :5001   │    │   :5002     │
         └────┬────┘  └────┬────┘    └──────┬──────┘
              │            │                │
              │       ┌────┴────┐           │
              │       │ Worker  │───────────┘
              │       │ Service │  (forwards logs via HTTP)
              │       └────┬────┘
              │            │
         ┌────┴────────────┴────┐
         │      RabbitMQ        │
         │   (message broker)   │
         └──────────┬───────────┘
                    │
              ┌─────┴─────┐
              │ PostgreSQL │
              │  (pgvector)│
              └────────────┘
```

## Network Isolation

Two Docker networks separate public and internal traffic:

- **public_net** — Nginx container only. This is the only entry point from the host machine.
- **internal_net** (`internal: true`) — Auth Service, FAQ Service, Worker, Logging Service, PostgreSQL, RabbitMQ. These containers cannot reach the internet and are not port-mapped to the host.

Nginx reverse-proxies requests to internal services based on URL path:
- `/api/auth/*` → auth-service:5000
- `/api/faq/*`, `/api/files/*`, `/api/admin/*` → faq-service:5001

## Authentication Flow

1. User sends POST `/api/auth/register` with credentials
2. Password is hashed with bcrypt (12 rounds) and stored
3. User sends POST `/api/auth/login` with email + password
4. Auth service validates credentials and returns JWT access token + refresh token
5. Client sends the access token in `Authorization: Bearer <token>` header
6. Each service verifies the JWT and extracts user ID and role
7. RBAC decorators (`@admin_required`) check the role before allowing access

## File Upload Security Pipeline

1. Client uploads file via multipart POST to `/api/files/upload`
2. Server validates: file exists, not empty, size ≤ 10MB
3. Extension check: only `.pdf`, `.txt`, `.docx` allowed
4. Blocked extensions: `.exe`, `.php`, `.js`, `.bat`, `.sh`
5. MIME type validation against expected types
6. SHA-256 hash calculated on raw bytes (before encryption)
7. File encrypted with Fernet (AES-128-CBC) using key from environment
8. Encrypted file stored with UUID filename in `/app/secure_uploads/` (outside web root)
9. Metadata (hash, encrypted path, original name) saved to `documents` table
10. Integrity can be verified later via `/api/files/<id>/verify` — decrypts in memory, re-hashes, compares

## Message Queue Architecture

RabbitMQ uses topic exchanges for event routing:

- `auth.exchange` — auth events (login success/failure, logout, registration)
- `document.exchange` — document events (upload, download, AI query, chunk request)

The Worker Service consumes from both queues, processes events (document chunking, embedding generation), and forwards structured log entries to the Logging Service via HTTP POST to `/internal/logs`.

The Monitoring Dashboard reads from `/api/logs` and `/api/logs/stats` to display real-time metrics.

## Rate Limiting

Configured in Nginx using `limit_req` zones:

| Zone | Endpoint | Rate | Burst |
|------|----------|------|-------|
| `login_limit` | `/api/auth/login` | 5 req/min | 3 |
| `auth_limit` | `/api/auth/*` | 10 req/min | 5 |
| `api_limit` | `/api/*` | 30 req/min | 10 |

Exceeding the limit returns HTTP 429.

## Service-to-Service Authentication

Internal services use `X-Internal-API-Key` header for mutual authentication. The key is shared via environment variables and is only known inside `internal_net`. Nginx strips this header from all incoming external requests, so external clients cannot impersonate internal services.
