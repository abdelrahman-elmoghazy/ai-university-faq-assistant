# Secure Distributed System — Final Project Report

## 1. Introduction

This project implements a secure distributed system for handling university FAQ queries using AI-powered responses. The system follows a microservices architecture deployed via Docker Compose, with a focus on security at every layer: authentication, authorization, encrypted storage, network isolation, and audit logging.

The system consists of 9 containerized services: an API gateway (Nginx), authentication service, FAQ service, worker service, logging service, monitoring dashboard, React frontend, PostgreSQL database, and RabbitMQ message broker.

---

## 2. System Architecture

### 2.1 Service Overview

The system is split into independently deployable services, each running in its own Docker container:

| Service | Technology | Role |
|---------|-----------|------|
| API Gateway | Nginx 1.25 | HTTPS termination, reverse proxy, rate limiting |
| Auth Service | Flask (Python) | User registration, login, JWT, RBAC |
| FAQ Service | Flask (Python) | Question handling, AI responses, file management |
| Worker Service | Python | Background processing, document chunking |
| Logging Service | Flask + Gunicorn | Centralized audit log storage |
| Monitoring Dashboard | Static HTML/JS | Real-time system monitoring |
| Frontend | React 18 + Vite | User interface |
| Database | PostgreSQL 15 + pgvector | Persistent storage |
| Message Broker | RabbitMQ 3.12 | Async event communication |

### 2.2 Network Topology

Two Docker bridge networks enforce separation:

- **public_net**: Only the Nginx container is attached. It binds to host ports 80 and 443.
- **internal_net** (with `internal: true`): All backend services communicate here. The `internal: true` flag prevents these containers from accessing the internet or being accessed directly from the host.

This means no backend service (database, auth, FAQ, etc.) has any port exposed to the outside. All external traffic goes through Nginx.

### 2.3 Architecture Diagram

> *[Insert architecture diagram here — show all 9 containers, the two networks, and traffic flow]*

---

## 3. Authentication and Authorization

### 3.1 JWT Authentication

The auth service handles user registration and login. On successful login, the server returns two tokens:

- **Access token**: Short-lived (configurable, default 24h), used for API requests
- **Refresh token**: Longer-lived (7 days), used to obtain new access tokens

Tokens are signed with HS256 using a secret key stored in environment variables. Each protected endpoint uses a `@token_required` decorator that:
1. Extracts the token from the `Authorization: Bearer` header
2. Verifies the signature and expiration
3. Loads the user from the database
4. Passes the user object to the route handler

### 3.2 Password Hashing

Passwords are hashed using bcrypt with 12 rounds of salting. The stored hash format is `$2b$12$...`. Plaintext passwords are never stored or logged.

### 3.3 Role-Based Access Control (RBAC)

The database has three tables for RBAC:

- `roles` — defines roles (admin, user)
- `permissions` — defines granular permissions (manage_users, upload_documents, etc.)
- `user_roles` — maps users to roles

Admin-only endpoints use an `@admin_required` decorator that checks the user's role before allowing access. A normal user trying to access `/api/admin/*` receives a 403 Forbidden response.

### 3.4 OAuth2

The system supports OAuth2 login via Google and GitHub. The flow:
1. Frontend redirects user to provider's authorization page
2. Provider redirects back with an authorization code
3. Backend exchanges the code for user profile information
4. If the email exists, the user is logged in; otherwise, a new account is created and linked

OAuth credentials are stored in `.env` and are not committed to version control.

---

## 4. API Gateway and Network Security

### 4.1 Nginx Reverse Proxy

Nginx serves as the single entry point. It routes requests based on URL prefix:

| Path | Upstream |
|------|----------|
| `/api/auth/*` | auth-service:5000 |
| `/api/faq/*`, `/api/files/*`, `/api/admin/*` | faq-service:5001 |
| `/` | frontend:80 |

### 4.2 HTTPS

Nginx listens on port 443 with TLS enabled. Self-signed certificates are used for development (generated via `scripts/generate_certs.sh`). Port 80 redirects all traffic to 443 using a dedicated redirect config (`00_redirect.conf`).

### 4.3 Rate Limiting

Three rate limiting zones are configured in Nginx:

| Zone | Target | Rate | Burst |
|------|--------|------|-------|
| login_limit | `/api/auth/login` | 5 req/min | 3 |
| auth_limit | `/api/auth/*` | 10 req/min | 5 |
| api_limit | `/api/*` | 30 req/min | 10 |

Exceeding the limit returns HTTP 429 (Too Many Requests). This protects against brute-force login attempts.

### 4.4 Security Headers

Every response from Nginx includes:

- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'`
- `Referrer-Policy: strict-origin-when-cross-origin`

### 4.5 Request Size Limiting

`client_max_body_size` is set to limit upload sizes at the gateway level before requests reach the backend.

---

## 5. Data Security

### 5.1 Database Schema

PostgreSQL stores all persistent data. Key tables:

| Table | Purpose |
|-------|---------|
| `users` | User accounts (email, username, bcrypt hash) |
| `roles` / `permissions` / `user_roles` | RBAC infrastructure |
| `documents` | File metadata, encrypted paths, SHA-256 hashes |
| `chunks` | Document text segments for search |
| `questions` / `answers` | AI chat history per user |
| `audit_logs` | Security event records |
| `service_logs` | Worker and service-level events |

Foreign keys enforce referential integrity. Ownership is checked at the application level — users can only access their own documents and questions.

### 5.2 Secure File Upload

The upload pipeline applies multiple validation steps:

1. Check that the file exists and is not empty
2. Validate file size (max 10MB)
3. Check file extension — only `.pdf`, `.txt`, `.docx` allowed
4. Block dangerous extensions: `.exe`, `.php`, `.js`, `.bat`, `.sh`
5. Validate MIME type matches the extension
6. Calculate SHA-256 hash of the raw file content
7. Encrypt the file using Fernet (AES-128-CBC + HMAC-SHA256)
8. Save with a random UUID filename to `/app/secure_uploads/` (outside the web root)
9. Store metadata in the `documents` table

### 5.3 File Encryption

Files are encrypted at rest using the Fernet symmetric encryption scheme from Python's `cryptography` library. The encryption key is stored in the `FILE_ENCRYPTION_KEY` environment variable.

Encrypted files are stored with `.enc` extension. Decryption only happens in memory when an authorized user requests the file via the API — decrypted content is never written to disk.

### 5.4 Integrity Verification

Before encryption, a SHA-256 hash of the raw file is computed and stored in the database. The `/api/files/<id>/verify` endpoint:
1. Reads the encrypted file from disk
2. Decrypts it in memory
3. Computes SHA-256 of the decrypted content
4. Compares with the stored hash
5. Returns `valid` or `modified_or_corrupted`

---

## 6. Message Queue and Background Processing

### 6.1 RabbitMQ Configuration

RabbitMQ is configured with:
- Custom credentials (no default guest/guest account)
- Two topic exchanges: `auth.exchange` and `document.exchange`
- Corresponding queues: `auth.events` and `document.events`
- Port 5672 exposed only on `internal_net` (not accessible from host)
- Management UI (15672) accessible only through Nginx with basic auth

### 6.2 Event Flow

When a user logs in, the auth service publishes an event to `auth.exchange` with routing key `auth.login.success` (or `auth.login.failed`). When a file is uploaded, the FAQ service publishes to `document.exchange` with routing key `document.uploaded`.

The worker service consumes from both queues:
- **Auth events** → forwarded to the logging service as audit entries
- **Document events** → triggers document chunking (splitting into overlapping 500-word segments) and logs the processing status

### 6.3 Worker Service

The worker runs as a long-lived process that connects to RabbitMQ and listens for messages. It uses a thread-safe connection with auto-reconnect logic. For document processing, it:
1. Receives the document event
2. Retrieves the document content
3. Splits text into overlapping chunks
4. Stores chunks in the `chunks` table
5. Reports job status to the logging service

---

## 7. Logging and Monitoring

### 7.1 Audit Trail

The logging service stores structured audit entries in the `service_logs` table. Each entry includes:
- `user_id` — who performed the action
- `action` — what happened (e.g., `successful_login`, `file_upload`, `unauthorized_access`)
- `source` — which service generated the event
- `ip_address` — client IP
- `status` — success or failure
- `details` — additional JSON metadata
- `created_at` — timestamp

### 7.2 Monitored Events

| Event | Source |
|-------|--------|
| Successful/failed login | Auth Service |
| User registration | Auth Service |
| Logout | Auth Service |
| File upload/download | FAQ Service |
| AI query | FAQ Service |
| Unauthorized access attempt | Auth/FAQ Services |
| Worker job status | Worker Service |

### 7.3 Monitoring Dashboard

A single-page HTML/JS application that polls the logging service API and displays:
- KPI counters (logins, uploads, AI queries, unauthorized attempts)
- Audit log table with filtering
- Event breakdown bar chart
- Worker job status panel

The dashboard auto-refreshes every 30 seconds.

---

## 8. Security Testing

### 8.1 Authentication Tests

| Test | Command | Expected Result |
|------|---------|-----------------|
| Register valid user | `curl -k -X POST https://localhost/api/auth/register -H "Content-Type: application/json" -d '{"username":"testuser","email":"test@uni.edu","password":"Password123!","full_name":"Test User"}'` | 201 Created |
| Login with correct credentials | `curl -k -X POST https://localhost/api/auth/login -H "Content-Type: application/json" -d '{"email":"test@uni.edu","password":"Password123!"}'` | 200 OK with tokens |
| Access protected route without token | `curl -k https://localhost/api/faq/history` | 401 Unauthorized |
| Access admin route as normal user | `curl -k -H "Authorization: Bearer <user_token>" https://localhost/api/admin/stats` | 403 Forbidden |

### 8.2 Rate Limiting Tests

Sending more than 5 login requests within one minute:

```bash
for i in $(seq 1 10); do
  curl -k -s -o /dev/null -w "%{http_code}\n" -X POST https://localhost/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@uni.edu","password":"wrong"}'
done
```

Expected: first 5 return 401, remaining return 429.

### 8.3 File Security Tests

| Test | Action | Expected |
|------|--------|----------|
| Upload valid PDF | POST `.pdf` file | 201 Created, file encrypted |
| Upload blocked extension | POST `.exe` file | 400 Bad Request |
| Upload oversized file | POST >10MB file | 400 Bad Request |
| Upload wrong MIME | POST file with mismatched MIME | 400 Bad Request |

### 8.4 Infrastructure Tests

The `scripts/test_infra.sh` script runs 12 automated checks:
1. HTTP → HTTPS redirect works
2. HTTPS health endpoint returns 200
3. TLS version is 1.2 or 1.3
4. Security headers present in responses
5. Nginx version hidden
6. `X-Internal-API-Key` stripped from external requests
7. Login rate limit triggers correctly
8. Admin endpoint requires authentication
9. Profile endpoint rejects invalid tokens
10. RabbitMQ port 5672 not publicly accessible
11. PostgreSQL port 5432 not publicly accessible
12. Unknown paths return 404

> *[Insert screenshots of test results here]*

---

## 9. Challenges and Limitations

- **Vector database**: We used pgvector inside PostgreSQL instead of a standalone vector database like Qdrant. This simplified deployment but limits search performance for large document collections.
- **OAuth credentials**: Google and GitHub OAuth is implemented in code but requires valid client credentials to test in production. The flow was verified with the code logic and mock testing.
- **Self-signed certificates**: HTTPS uses self-signed certificates for development. In production, these would be replaced with Let's Encrypt certificates.
- **AI provider dependency**: The AI service falls back to a mock provider when no API key is configured, which returns keyword-based responses instead of actual LLM output.

---

## 10. Conclusion

The project implements a distributed microservices system with 20 security features covering authentication, authorization, encryption, network isolation, audit logging, and secure communication. All services are containerized and orchestrated with Docker Compose, with proper separation between public and internal networks. The system demonstrates practical application of secure distributed system design principles in a university FAQ context.

---

## Appendix

### A. How to Run

```bash
cp .env.example .env
# Fill in all CHANGE_ME values
bash scripts/generate_certs.sh localhost
docker compose up --build
```

### B. Default Ports

| Service | Port |
|---------|------|
| Frontend | http://localhost:3000 |
| API Gateway | https://localhost (443) |
| Monitoring | http://localhost:8081 |

### C. Environment Variables

See `.env.example` for the full list of required configuration variables.
