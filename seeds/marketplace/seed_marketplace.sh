#!/usr/bin/env bash
# Ejecuta el seed del marketplace desde cualquier carpeta
# Uso:
#   ./src/seeds/marketplace/seed_marketplace.sh [letdem.settings.staging]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANAGE_DIR="${SCRIPT_DIR}/../../"

cd "$MANAGE_DIR"

if [[ "$#" -ge 1 ]]; then
  export DJANGO_SETTINGS_MODULE="$1"
fi

python manage.py populate_marketplace
