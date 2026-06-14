#!/usr/bin/env bash
# CIEL TUI Launcher
# Starts the Ink TUI with the Gateway backend.
# Usage: ./run.sh [--gateway-only|--tui-only] [--python python3]

set -euo pipefail

CIEL_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
INK_DIR="$CIEL_ROOT/ciel/interfaces/tui/ink"
GATEWAY_MODULE="ciel.interfaces.tui.gateway.server"
PYTHON="${CIEL_PYTHON:-python3}"

MODE="${1:-all}"
shift || true

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━ CIEL TUI ━━━${NC}"
echo -e "${GREEN}Root:${NC}  $CIEL_ROOT"
echo -e "${GREEN}Python:${NC} $PYTHON"

start_gateway() {
    echo -e "${YELLOW}Starting Gateway (JSON-RPC over stdio)...${NC}"
    cd "$CIEL_ROOT"
    PYTHONPATH="$CIEL_ROOT:$PYTHONPATH" exec "$PYTHON" -m "$GATEWAY_MODULE"
}

start_tui() {
    echo -e "${YELLOW}Starting Ink TUI...${NC}"
    cd "$INK_DIR"

    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing npm dependencies...${NC}"
        npm install
    fi

    CIEL_PYTHON="$PYTHON" \
    CIEL_CWD="$CIEL_ROOT" \
    CIEL_GATEWAY_ARGS="--python $PYTHON" \
    npx vite build --mode development 2>/dev/null || true

    # Run via ts-node/tsx for development, or built JS
    if [ -f "dist/ciel-tui.mjs" ]; then
        CIEL_PYTHON="$PYTHON" CIEL_CWD="$CIEL_ROOT" node dist/ciel-tui.mjs
    else
        echo -e "${YELLOW}Dev mode: using tsx...${NC}"
        CIEL_PYTHON="$PYTHON" CIEL_CWD="$CIEL_ROOT" npx tsx src/main.tsx
    fi
}

case "$MODE" in
    --gateway-only|gateway)
        start_gateway
        ;;
    --tui-only|tui)
        start_tui
        ;;
    --test|test)
        echo -e "${YELLOW}Running gateway tests...${NC}"
        cd "$CIEL_ROOT"
        PYTHONPATH="$CIEL_ROOT:$PYTHONPATH" "$PYTHON" -m pytest \
            ciel/interfaces/tui/gateway/test_gateway.py \
            -v --tb=short "$@"
        ;;
    *)
        # Run gateway in background, TUI in foreground
        echo -e "${GREEN}Starting Gateway (background) + TUI (foreground)${NC}"
        start_gateway &
        GATEWAY_PID=$!
        sleep 1
        start_tui
        kill $GATEWAY_PID 2>/dev/null || true
        ;;
esac
