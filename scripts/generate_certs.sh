#!/bin/bash
# ============================================================
#  generate_certs.sh
#  Generates self-signed SSL certs for local/dev use.
#  For production: replace with Let's Encrypt (see below).
# ============================================================

set -euo pipefail

CERTS_DIR="$(dirname "$0")/../nginx/certs"
DOMAIN="${1:-localhost}"

echo "📁 Creating certs directory..."
mkdir -p "$CERTS_DIR"

# ── DH Parameters (2048-bit) ─────────────────────────────
if [ ! -f "$CERTS_DIR/dhparam.pem" ]; then
    echo "🔐 Generating DH parameters (this may take a while)..."
    openssl dhparam -out "$CERTS_DIR/dhparam.pem" 2048
else
    echo "✅ DH parameters already exist, skipping."
fi

# ── Self-signed certificate ───────────────────────────────
echo "🔑 Generating self-signed certificate for: $DOMAIN"
openssl req -x509 \
    -newkey rsa:4096 \
    -keyout "$CERTS_DIR/privkey.pem" \
    -out    "$CERTS_DIR/fullchain.pem" \
    -days   365 \
    -nodes \
    -subj   "/C=US/ST=State/L=City/O=AI University/CN=$DOMAIN" \
    -addext "subjectAltName=DNS:$DOMAIN,DNS:www.$DOMAIN,IP:127.0.0.1"

echo ""
echo "✅ Certificates generated in: $CERTS_DIR"
echo ""
echo "📌 For PRODUCTION — use Let's Encrypt instead:"
echo "   1. Install certbot: apt install certbot python3-certbot-nginx"
echo "   2. Run: certbot --nginx -d $DOMAIN"
echo "   3. Copy certs to nginx/certs/ or update nginx.conf paths"
echo "   4. Setup auto-renewal: certbot renew --dry-run"

# ── htpasswd for RabbitMQ Management UI ──────────────────
if ! command -v htpasswd &>/dev/null; then
    echo ""
    echo "⚠️  htpasswd not found. Install apache2-utils:"
    echo "   apt install apache2-utils"
else
    echo ""
    echo "🔒 Creating htpasswd for RabbitMQ Management UI..."
    read -r -p "Enter admin username [admin]: " HTUSER
    HTUSER="${HTUSER:-admin}"
    htpasswd -c "$CERTS_DIR/.htpasswd" "$HTUSER"
    echo "✅ htpasswd saved to $CERTS_DIR/.htpasswd"
fi