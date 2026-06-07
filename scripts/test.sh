#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# CIEL v∞.2 — Test runner shell
# Wrapper autour de pytest avec output colorisé et résumé
# ─────────────────────────────────────────────────────────────
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   CIEL v∞.2 — TEST RUNNER                                ║${NC}"
echo -e "${BLUE}║   Phase 0 : ÉVEIL                                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo

# ── Args ────────────────────────────────────────────────────
TARGET="${1:-tests/}"
EXTRA="${2:-}"

# ── Run pytest ──────────────────────────────────────────────
python3 -m pytest "$TARGET" \
  -v \
  --tb=short \
  --color=yes \
  --durations=10 \
  $EXTRA

EXIT_CODE=$?

echo
if [[ $EXIT_CODE -eq 0 ]]; then
  echo -e "  ${GREEN}✓ Tous les tests passent${NC}"
else
  echo -e "  ${RED}✗ $EXIT_CODE tests ont échoué${NC}"
fi
echo

exit $EXIT_CODE
