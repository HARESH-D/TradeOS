#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.production"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.prod.yml"
BACKUP_DIR="$SCRIPT_DIR/backups"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$BACKUP_DIR"
umask 077
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T db \
  pg_dump -U tradeos -d tradeos | gzip > "$BACKUP_DIR/tradeos-$STAMP.sql.gz"

find "$BACKUP_DIR" -type f -name 'tradeos-*.sql.gz' -mtime +14 -delete
echo "Created $BACKUP_DIR/tradeos-$STAMP.sql.gz"

