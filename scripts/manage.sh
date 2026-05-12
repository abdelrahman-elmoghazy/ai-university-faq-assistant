#!/bin/bash
# ============================================================
#  manage.sh — Infrastructure Management Script
#  Usage: ./scripts/manage.sh [command]
# ============================================================

set -euo pipefail

COMPOSE_FILE="$(dirname "$0")/../docker-compose.yml"
ENV_FILE="$(dirname "$0")/../.env"

# ── Colors ───────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Helpers ──────────────────────────────────────────────
check_env() {
    if [ ! -f "$ENV_FILE" ]; then
        warn ".env not found. Copying from .env.example..."
        cp "$(dirname "$0")/../.env.example" "$ENV_FILE"
        error "Please fill in .env with real values before starting."
    fi

    # Validate no CHANGE_ME placeholders remain
    if grep -q "CHANGE_ME" "$ENV_FILE"; then
        error ".env still contains CHANGE_ME placeholders. Please set real secrets."
    fi
    info ".env validation passed ✅"
}

check_certs() {
    CERT_DIR="$(dirname "$0")/../nginx/certs"
    if [ ! -f "$CERT_DIR/fullchain.pem" ] || [ ! -f "$CERT_DIR/privkey.pem" ]; then
        warn "SSL certificates not found. Generating self-signed certs..."
        bash "$(dirname "$0")/generate_certs.sh"
    fi
}

# ── Commands ─────────────────────────────────────────────
cmd_up() {
    info "Starting AI University FAQ Assistant infrastructure..."
    check_env
    check_certs
    docker compose -f "$COMPOSE_FILE" up -d --build
    info "All services started. Run './scripts/manage.sh status' to check."
}

cmd_down() {
    info "Stopping all services..."
    docker compose -f "$COMPOSE_FILE" down
}

cmd_restart() {
    cmd_down
    cmd_up
}

cmd_status() {
    docker compose -f "$COMPOSE_FILE" ps
}

cmd_logs() {
    SERVICE="${2:-}"
    docker compose -f "$COMPOSE_FILE" logs -f --tail=100 $SERVICE
}

cmd_test() {
    info "Running infrastructure tests..."
    bash "$(dirname "$0")/test_infra.sh"
}

cmd_rotate_secrets() {
    info "Generating new secrets..."
    echo "JWT_SECRET_KEY=$(openssl rand -hex 64)"
    echo "INTERNAL_API_KEY=$(openssl rand -hex 32)"
    echo "SERVICE_SECRET=$(openssl rand -hex 32)"
    warn "Copy the above values into your .env file, then restart the stack."
}

# ── Dispatch ─────────────────────────────────────────────
COMMAND="${1:-help}"
case "$COMMAND" in
    up)              cmd_up ;;
    down)            cmd_down ;;
    restart)         cmd_restart ;;
    status)          cmd_status ;;
    logs)            cmd_logs "$@" ;;
    test)            cmd_test ;;
    rotate-secrets)  cmd_rotate_secrets ;;
    help|*)
        echo "Usage: $0 {up|down|restart|status|logs [service]|test|rotate-secrets}"
        ;;
esac