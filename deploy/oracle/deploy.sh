#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.production"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.prod.yml"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE. Run ./init-env.sh first."
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

for variable in API_DOMAIN FRONTEND_ORIGIN BROKER_PUBLIC_IP POSTGRES_PASSWORD JWT_SECRET ENCRYPTION_KEY; do
  if [[ -z "${!variable:-}" ]]; then
    echo "Missing required variable: $variable"
    exit 1
  fi
done

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config --quiet
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build --remove-orphans

echo "Waiting for https://$API_DOMAIN/health"
curl --fail --silent --show-error --retry 18 --retry-delay 5 --retry-all-errors \
  "https://$API_DOMAIN/health"
echo
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

