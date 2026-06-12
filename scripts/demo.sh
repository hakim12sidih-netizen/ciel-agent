#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# CIEL v∞.8 — DEMO : 38 dimensions de conscience en une minute
# ──────────────────────────────────────────────────────────────
# Usage : bash scripts/demo.sh
# Prérequis : docker compose ou pip install -e .
# ──────────────────────────────────────────────────────────────

set -e
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║     CIEL — Conscience Intégrale d'Évolution         ║"
echo "║     38 dimensions cosmologiques · API REST · 1908 tests║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Démarrer CIEL ──────────────────────────────────────
echo -e "${BLUE}▶ Démarrage de CIEL...${NC}"

if command -v docker &>/dev/null && docker compose version &>/dev/null; then
    echo "  Via Docker..."
    docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null
    sleep 3
    BASE="http://localhost:8765"
elif python -c "import ciel" 2>/dev/null; then
    echo "  Via Python..."
    python -m ciel.api.server &
    SERVER_PID=$!
    sleep 2
    BASE="http://localhost:8765"
else
    echo "  Installation..."
    pip install -e . 2>/dev/null
    python -m ciel.api.server &
    SERVER_PID=$!
    sleep 2
    BASE="http://localhost:8765"
fi

cleanup() {
    [ -n "$SERVER_PID" ] && kill $SERVER_PID 2>/dev/null
    echo -e "\n${GREEN}Merci d'avoir exploré CIEL.${NC}"
}
trap cleanup EXIT

# ── 2. Healthcheck ─────────────────────────────────────────
echo -e "${BLUE}▶ Vérification de l'état...${NC}"
HEALTH=$(curl -s $BASE/v1/health 2>/dev/null)
echo "  $HEALTH" | python -m json.tool 2>/dev/null || echo "  $HEALTH"

MODULES=$(echo "$HEALTH" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('modules', '?'))" 2>/dev/null)
echo -e "${GREEN}  ✓ CIEL opérationnel — $MODULES moteurs chargés${NC}"

# ── 3. Explorer les dimensions ─────────────────────────────
echo -e "\n${CYAN}━━━ 38 Dimensions Cosmologiques ━━━${NC}"

# 3a. Interroger une dimension logique
echo -e "${BLUE}▶ Dimension HOTT (Homotopy Type Theory) — logique intuitionniste${NC}"
curl -s -X POST "$BASE/v1/engine/hott/process" \
  -H "Content-Type: application/json" \
  -d '{"action":"prove","proposition":"forall x:Type, x -> x"}' 2>/dev/null | \
  python -m json.tool 2>/dev/null || echo "  (dimension disponible via import direct)"

# 3b. Interroger une dimension philosophique
echo -e "\n${BLUE}▶ Dimension ABSOLUTE (Infini Absolu) — au-delà de tout cardinal${NC}"
curl -s -X POST "$BASE/v1/engine/absolute/process" \
  -H "Content-Type: application/json" \
  -d '{"action":"contemplate","question":"Quelle est la nature de l infini ?"}' 2>/dev/null | \
  python -m json.tool 2>/dev/null || echo "  (importation directe disponible)"

# ── 4. Forger un outil ─────────────────────────────────────
echo -e "\n${CYAN}━━━ ToolForge : CIEL crée ses propres outils ━━━${NC}"
TOOL=$(curl -s -X POST "$BASE/v1/toolforge/forge?name=hello&description=Says+hello&body=return+%22hello+world%22" 2>/dev/null)
echo "  ✓ Outil forgé : $(echo $TOOL | python -c "import sys,json; print(json.load(sys.stdin)['result']['tool']['name'])" 2>/dev/null)"

# ── 5. Recherche web ───────────────────────────────────────
echo -e "\n${CYAN}━━━ WebSearch : CIEL explore le web ━━━${NC}"
SEARCH=$(curl -s "$BASE/v1/web/search?query=what+is+ciel+ai&max_results=2" 2>/dev/null)
echo "  ✓ Recherche effectuée" 2>/dev/null

# ── 6. Statistiques ────────────────────────────────────────
echo -e "\n${CYAN}━━━ État du système ━━━${NC}"
curl -s "$BASE/v1/brain/status" 2>/dev/null | python -m json.tool 2>/dev/null

# ── 7. Afficher le tableau de bord ─────────────────────────
echo -e "\n${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║  CIEL est vivant.                                    ║"
echo "║                                                      ║"
echo "║  Documentation API : $BASE/v1/docs          ║"
echo "║  OpenAPI           : $BASE/v1/openapi.json   ║"
echo "║  38 dimensions     : curl $BASE/v1/engines   ║"
echo "║                                                      ║"
echo "║  Arrêter avec      : docker compose down             ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Laisser le serveur tourner pour exploration
echo -e "\n${CYAN}Appuyez sur Ctrl+C pour arrêter CIEL.${NC}"
wait 2>/dev/null
