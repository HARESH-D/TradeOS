#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.production"

if [[ -f "$ENV_FILE" ]]; then
  echo "$ENV_FILE already exists; refusing to overwrite it."
  exit 1
fi

read -r -p "Backend hostname without https:// (for example api.example.com): " API_DOMAIN
read -r -p "Vercel frontend origin (for example https://tradeos.vercel.app): " FRONTEND_ORIGIN
read -r -p "OCI reserved public IPv4: " BROKER_PUBLIC_IP

if [[ ! "$API_DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]]; then
  echo "Invalid backend hostname."
  exit 1
fi

if [[ ! "$FRONTEND_ORIGIN" =~ ^https:// ]]; then
  echo "The frontend origin must start with https://."
  exit 1
fi

if [[ ! "$BROKER_PUBLIC_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
  echo "The broker public IP must be an IPv4 address."
  exit 1
fi

IFS='.' read -r -a IP_OCTETS <<< "$BROKER_PUBLIC_IP"
for octet in "${IP_OCTETS[@]}"; do
  if (( 10#$octet > 255 )); then
    echo "The broker public IP contains an invalid octet: $octet"
    exit 1
  fi
done

POSTGRES_PASSWORD="$(openssl rand -hex 24)"
JWT_SECRET="$(openssl rand -hex 64)"
ENCRYPTION_KEY="$(openssl rand -base64 32 | tr '/+' '_-' | tr -d '\n')"

umask 077
cat > "$ENV_FILE" <<EOF
API_DOMAIN=$API_DOMAIN
FRONTEND_ORIGIN=$FRONTEND_ORIGIN
BROKER_PUBLIC_IP=$BROKER_PUBLIC_IP
BROKER_LOCAL_IP=
BROKER_MAC_ADDRESS=
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
JWT_SECRET=$JWT_SECRET
ENCRYPTION_KEY=$ENCRYPTION_KEY
EOF

echo "Created $ENV_FILE with mode 600. Keep this file off Git and back it up securely."
