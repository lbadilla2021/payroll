#!/bin/bash
set -e

# ── Ruta del script ──────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"


# ── Ruta al .env (un nivel arriba) ───────────────────────────────────────────
ENV_FILE="$SCRIPT_DIR/../.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ No se encontró archivo .env en: $ENV_FILE"
  exit 1
fi

# ── Cargar variables ─────────────────────────────────────────────────────────
set -o allexport
source "$ENV_FILE"
set +o allexport

# ── Variables ────────────────────────────────────────────────────────────────
DB_CONTAINER="db"

echo "▶ Conectando a PostgreSQL..."
echo "   DB: $POSTGRES_DB"
echo "   User: $POSTGRES_USER"
echo

docker compose exec "$DB_CONTAINER" psql \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB"