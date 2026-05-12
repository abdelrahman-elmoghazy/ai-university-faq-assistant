# Infrastructure Setup — Member 2: API Gateway & DevOps

## Overview

This document covers the complete infrastructure layer for the AI University FAQ Assistant. It sits on top of Member 1's Auth Service without modifying it.

```
Internet
    │
    ▼
[Nginx :443]  ←── HTTPS only, rate-limited, security headers
    │
    │  (internal_net — no public access)
    ├──► [auth-service :5000]
    ├──► [postgres :5432]
    └──► [rabbitmq :5672 / :15672]
```

---

## Directory Structure

```
project/
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Template — copy to .env
├── nginx/
│   ├── nginx.conf              # Main nginx config (rate limits, SSL defaults)
│   └── conf.d/
│       ├── 00_redirect.conf    # HTTP → HTTPS redirect
│       ├── 10_api_gateway.conf # HTTPS reverse proxy
│       └── 20_rabbitmq_mgmt.conf # RabbitMQ UI (basic auth protected)
├── rabbitmq/
│   ├── rabbitmq.conf           # Broker config (no guest/guest)
│   └── definitions.json        # Users, vhosts, queues
├── scripts/
│   ├── manage.sh               # Start / stop / test helper
│   ├── generate_certs.sh       # SSL cert generation
│   └── test_infra.sh           # Infrastructure test suite
└── docs/
    └── INFRASTRUCTURE.md       # This file
```

---

## Quick Start

### 1. Setup environment

```bash
cp .env.example .env
# Edit .env — fill in every CHANGE_ME value
```

### 2. Generate secrets

```bash
# JWT secret
echo "JWT_SECRET_KEY=$(openssl rand -hex 64)"

# Internal API key
echo "INTERNAL_API_KEY=$(openssl rand -hex 32)"

# Service secret
echo "SERVICE_SECRET=$(openssl rand -hex 32)"
```

Paste the output into `.env`.

### 3. Generate SSL certificates

```bash
# Development (self-signed)
bash scripts/generate_certs.sh yourdomain.com

# Production (Let's Encrypt)
certbot certonly --standalone -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/certs/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem   nginx/certs/
openssl dhparam -out nginx/certs/dhparam.pem 2048
```

### 4. Start the stack

```bash
bash scripts/manage.sh up
```

### 5. Run tests

```bash
bash scripts/manage.sh test
```

---

## Nginx API Gateway

### Rate Limiting Zones

| Zone         | Endpoint              | Rate    | Burst |
|--------------|-----------------------|---------|-------|
| `login_limit`| `/api/auth/login`     | 5/min   | 3     |
| `auth_limit` | `/api/auth/*`         | 10/min  | 5     |
| `api_limit`  | `/api/*` (all others) | 30/min  | 10    |

Rate limit violations return **HTTP 429** with a JSON body.

### Security Headers

Every response includes:

| Header | Value |
|--------|-------|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` |
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Content-Security-Policy` | `default-src 'self'; frame-ancestors 'none'` |

### Internal Key Protection

`X-Internal-API-Key` is **stripped** by Nginx on all incoming requests. External clients cannot impersonate internal services.

---

## Container Networking

### `public_net` (bridge)
- Only `nginx` container is attached.
- Nginx listens on ports 80 and 443 on the host.

### `internal_net` (bridge, `internal: true`)
- All backend services: `auth-service`, `postgres`, `rabbitmq`.
- `internal: true` means **no outbound internet access** from these containers.
- Services are NOT port-mapped to the host — only reachable via Nginx.

---

## RabbitMQ Security

### What's configured

- **Guest account disabled** — `definitions.json` overrides the default guest user with no password hash, effectively disabling it.
- **Custom credentials** — set via `RABBITMQ_USER` / `RABBITMQ_PASSWORD` in `.env`.
- **AMQP port 5672** — exposed only on `internal_net`, not the host.
- **Management UI port 15672** — exposed only on `internal_net`; accessed through Nginx with HTTP Basic Auth.
- **Loopback restriction** removed — services on internal_net can connect with credentials.

### Connecting from auth-service

```python
import pika, os

credentials = pika.PlainCredentials(
    os.getenv('RABBITMQ_USER'),
    os.getenv('RABBITMQ_PASSWORD')
)
params = pika.ConnectionParameters(
    host='rabbitmq',
    port=5672,
    virtual_host=os.getenv('RABBITMQ_VHOST', '/'),
    credentials=credentials
)
connection = pika.BlockingConnection(params)
```

---

## Secrets Management

### Rules
1. **Never** commit `.env` to version control (already in `.gitignore`).
2. All secrets generated with `openssl rand` (cryptographically random).
3. Production: use a secrets manager (AWS Secrets Manager, HashiCorp Vault, Docker Secrets).
4. Rotate secrets with: `bash scripts/manage.sh rotate-secrets`

### Secret rotation procedure
1. Generate new values: `bash scripts/manage.sh rotate-secrets`
2. Update `.env`
3. Restart: `bash scripts/manage.sh restart`

---

## Service-to-Service Authentication

Internal services authenticate to each other using the `X-Internal-API-Key` header:

```http
GET /api/internal/verify HTTP/1.1
Host: auth-service
X-Internal-API-Key: <INTERNAL_API_KEY from .env>
```

This key is:
- Generated with `openssl rand -hex 32`
- Known only to services inside `internal_net`
- Stripped by Nginx on all public requests (cannot be spoofed from outside)

---

## Infrastructure Tests

Run the full test suite:

```bash
bash scripts/test_infra.sh
```

### Tests covered

| # | Test |
|---|------|
| 1 | HTTP → HTTPS redirect |
| 2 | HTTPS health endpoint returns 200 |
| 3 | TLS version is 1.2 or 1.3 |
| 4 | All security headers present |
| 5 | Nginx version hidden |
| 6 | `X-Internal-API-Key` stripped on ingress |
| 7 | Login rate limit triggers at 5 req/min |
| 8 | Admin endpoint returns 401 without token |
| 9 | Profile endpoint rejects invalid token |
| 10 | RabbitMQ port 5672 not publicly exposed |
| 11 | PostgreSQL port 5432 not publicly exposed |
| 12 | Unknown paths return 404 |

---

## Production Checklist

- [ ] `.env` has no `CHANGE_ME` values
- [ ] SSL certs from Let's Encrypt (not self-signed)
- [ ] `dhparam.pem` generated (2048-bit minimum)
- [ ] `.htpasswd` created for RabbitMQ Management UI
- [ ] IP allowlist enabled in `20_rabbitmq_mgmt.conf`
- [ ] `server_name` updated in nginx conf files
- [ ] `CORS_ORIGINS` set to production domain only
- [ ] All `CHANGE_ME` oauth redirect URIs updated
- [ ] Log rotation configured (`/var/log/nginx/`)
- [ ] `bash scripts/manage.sh test` passes all checks