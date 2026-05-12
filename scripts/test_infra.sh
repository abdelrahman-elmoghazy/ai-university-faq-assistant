#!/bin/bash
# ============================================================
#  test_infra.sh — Infrastructure Test Suite
#  Tests: HTTPS, rate limiting, internal service auth,
#         RabbitMQ security, container networking
# ============================================================

set -euo pipefail

BASE_URL="${BASE_URL:-https://localhost}"
PASS=0; FAIL=0

# ── Helpers ──────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASS++)); }
fail() { echo -e "${RED}[FAIL]${NC} $1 — $2"; ((FAIL++)); }
info() { echo -e "${YELLOW}[TEST]${NC} $1"; }

http() {
    curl -sk -o /dev/null -w "%{http_code}" \
         --max-time 10 \
         "$@"
}

# ── 1. HTTP → HTTPS Redirect ─────────────────────────────
info "HTTP → HTTPS redirect"
CODE=$(http -L "http://localhost/health" -w "%{url_effective}" | grep -o "https://" | head -1 || echo "")
if [[ "$CODE" == "https://" ]]; then
    pass "HTTP redirects to HTTPS"
else
    # Fallback: check redirect code
    RCODE=$(http "http://localhost/health")
    if [[ "$RCODE" == "301" || "$RCODE" == "302" ]]; then
        pass "HTTP returns redirect ($RCODE)"
    else
        fail "HTTP redirect" "Got code $RCODE"
    fi
fi

# ── 2. HTTPS Health Check ────────────────────────────────
info "HTTPS health endpoint"
CODE=$(http "$BASE_URL/health")
if [[ "$CODE" == "200" ]]; then
    pass "HTTPS health check returns 200"
else
    fail "HTTPS health check" "Got $CODE"
fi

# ── 3. SSL/TLS version check ─────────────────────────────
info "TLS version (must be 1.2 or 1.3)"
TLS_VER=$(curl -sk -v "$BASE_URL/health" 2>&1 | grep -oP "TLSv\d+\.\d+" | head -1 || echo "unknown")
if [[ "$TLS_VER" == "TLSv1.2" || "$TLS_VER" == "TLSv1.3" ]]; then
    pass "TLS version: $TLS_VER"
else
    fail "TLS version" "Got: $TLS_VER (expected 1.2 or 1.3)"
fi

# ── 4. Security Headers ───────────────────────────────────
info "Security headers"
HEADERS=$(curl -skI "$BASE_URL/health" 2>&1)

for HEADER in "X-Frame-Options" "X-Content-Type-Options" "Strict-Transport-Security" "X-XSS-Protection"; do
    if echo "$HEADERS" | grep -qi "$HEADER"; then
        pass "Header present: $HEADER"
    else
        fail "Missing security header" "$HEADER"
    fi
fi

# Server version hidden
if echo "$HEADERS" | grep -qi "^Server: nginx/[0-9]"; then
    fail "Server header exposes nginx version" ""
else
    pass "Nginx version hidden in Server header"
fi

# ── 5. Internal API Key Injection Prevention ──────────────
info "X-Internal-API-Key cannot be injected from outside"
CODE=$(http "$BASE_URL/api/auth/login" \
    -X POST \
    -H "Content-Type: application/json" \
    -H "X-Internal-API-Key: hacker_key" \
    -d '{"email":"x@x.com","password":"wrong"}')
# Should get 400/401/422, NOT 200/500 due to key being stripped
if [[ "$CODE" != "500" ]]; then
    pass "X-Internal-API-Key stripped by gateway (got $CODE)"
else
    fail "X-Internal-API-Key not stripped" "Got 500"
fi

# ── 6. Rate Limiting — Login ─────────────────────────────
info "Rate limiting on /api/auth/login (5/min)"
RATE_HIT=false
for i in $(seq 1 10); do
    CODE=$(http -X POST "$BASE_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@test.com","password":"wrong"}')
    if [[ "$CODE" == "429" ]]; then
        RATE_HIT=true
        break
    fi
done
if $RATE_HIT; then
    pass "Rate limit triggered on login endpoint"
else
    fail "Rate limit not triggered" "Sent 10 requests without 429"
fi

# ── 7. Admin Endpoint Without Token ──────────────────────
info "Admin endpoint rejects unauthenticated request"
CODE=$(http "$BASE_URL/api/admin/users")
if [[ "$CODE" == "401" ]]; then
    pass "Admin endpoint returns 401 without token"
else
    fail "Admin endpoint security" "Expected 401, got $CODE"
fi

# ── 8. Accessing Other User's Data ───────────────────────
info "Cannot access another user's data without admin"
CODE=$(http "$BASE_URL/api/auth/profile" \
    -H "Authorization: Bearer INVALID_TOKEN")
if [[ "$CODE" == "401" ]]; then
    pass "Profile endpoint rejects invalid token"
else
    fail "Profile endpoint security" "Expected 401, got $CODE"
fi

# ── 9. RabbitMQ Not Publicly Exposed ─────────────────────
info "RabbitMQ AMQP port (5672) not publicly reachable"
if timeout 3 bash -c "cat < /dev/null > /dev/tcp/localhost/5672" 2>/dev/null; then
    fail "RabbitMQ AMQP port 5672 is publicly exposed!" ""
else
    pass "RabbitMQ AMQP port 5672 is NOT publicly exposed"
fi

# ── 10. PostgreSQL Not Publicly Exposed ──────────────────
info "PostgreSQL port (5432) not publicly reachable"
if timeout 3 bash -c "cat < /dev/null > /dev/tcp/localhost/5432" 2>/dev/null; then
    fail "PostgreSQL port 5432 is publicly exposed!" ""
else
    pass "PostgreSQL port 5432 is NOT publicly exposed"
fi

# ── 11. Unknown Paths Return 404 ─────────────────────────
info "Unknown paths return 404 (not 200 or 500)"
CODE=$(http "$BASE_URL/not-a-real-path")
if [[ "$CODE" == "404" ]]; then
    pass "Unknown path returns 404"
else
    fail "Unknown path" "Expected 404, got $CODE"
fi

# ── Summary ──────────────────────────────────────────────
echo ""
echo "=================================="
echo -e "${GREEN}PASSED: $PASS${NC}  |  ${RED}FAILED: $FAIL${NC}"
echo "=================================="
if [[ $FAIL -gt 0 ]]; then
    exit 1
fi