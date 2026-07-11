#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.production"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.prod.yml"

set -a
source "$ENV_FILE"
set +a

ACTUAL_IP="$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T api \
  python -c "import urllib.request; print(urllib.request.urlopen('https://api.ipify.org', timeout=10).read().decode())")"

echo "Configured Angel One IP: $BROKER_PUBLIC_IP"
echo "Observed API egress IP:  $ACTUAL_IP"

if [[ "$ACTUAL_IP" != "$BROKER_PUBLIC_IP" ]]; then
  echo "ERROR: The API is not leaving through the registered static IPv4."
  exit 1
fi

echo "Egress IP verification passed."

