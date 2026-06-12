#!/bin/bash
set -euo pipefail

# ── CIEL Installer ─────────────────────────────────────
# Usage: curl -fsSL https://ciel.ai/install.sh | bash
#   or:  curl -fsSL https://ciel.ai/install.sh | bash -s -- --help
# ────────────────────────────────────────────────────────

BOLD='\033[1m'
DIM='\033[2m'
BLUE='\033[38;2;88;166;255m'
GREEN='\033[38;2;63;185;80m'
RED='\033[38;2;248;81;73m'
YEL='\033[38;2;210;153;34m'
CYAN='\033[38;2;88;166;255m'
NC='\033[0m'

CIEL_VERSION="${CIEL_VERSION:-latest}"
CIEL_HOME="${CIEL_HOME:-$HOME/.ciel}"
PYTHON_MIN="3.12"
NODE_MIN_MAJOR=18

TMPDIR=""
cleanup() { [[ -n "$TMPDIR" ]] && rm -rf "$TMPDIR" 2>/dev/null || true; }
trap cleanup EXIT

log()  { printf "${BLUE}ℹ${NC} %s\n" "$*"; }
ok()   { printf "${GREEN}✓${NC} %s\n" "$*"; }
warn() { printf "${YEL}⚠${NC} %s\n" "$*"; }
err()  { printf "${RED}✗${NC} %s\n" "$*"; }
header() {
    printf "\n${CYAN}╔══════════════════════════════════════╗${NC}\n"
    printf "${CYAN}║        ${BOLD}CIEL${NC}${CYAN} — Installation          ║${NC}\n"
    printf "${CYAN}╚══════════════════════════════════════╝${NC}\n\n"
}

usage() {
    cat <<EOF
Usage: curl -fsSL https://ciel.ai/install.sh | bash [options]

Options:
  --help          Affiche cette aide
  --no-prompt     Mode non-interactif
  --dev           Installation complète (deps dev + test)
  --minimal       Installation minimale (Python seulement)
  --port PORT     Port du serveur (défaut: 8765)
  --provider STR  Fournisseur LLM (défaut: openai)
  --model STR     Modèle LLM (défaut: gpt-4o)
  --auto-start    Active le redémarrage automatique au boot
EOF
    exit 0
}

# Parse args
NO_PROMPT=0
INSTALL_MODE="standard"
API_PORT=8765
LLM_PROVIDER="openai"
LLM_MODEL="gpt-4o"
AUTO_START=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help) usage ;;
        --no-prompt) NO_PROMPT=1 ;;
        --dev) INSTALL_MODE="dev" ;;
        --minimal) INSTALL_MODE="minimal" ;;
        --port) API_PORT="$2"; shift ;;
        --provider) LLM_PROVIDER="$2"; shift ;;
        --model) LLM_MODEL="$2"; shift ;;
        --auto-start) AUTO_START=1 ;;
        *) err "Option inconnue: $1"; usage ;;
    esac
    shift
done

# ── Detect OS ──
OS="$(uname -s)"
ARCH="$(uname -m)"
case "$OS" in
    Linux)  OS="linux" ;;
    Darwin) OS="macos" ;;
    *)      err "OS non supporté: $OS"; exit 1 ;;
esac
case "$ARCH" in
    x86_64|amd64) ARCH="x86_64" ;;
    aarch64|arm64) ARCH="aarch64" ;;
    *) warn "Architecture non testée: $ARCH" ;;
esac

# ── Detect package manager ──
PKG_MGR=""
INSTALL_CMD=""
if command -v apt-get &>/dev/null; then
    PKG_MGR="apt"
    INSTALL_CMD="apt-get install -y"
elif command -v dnf &>/dev/null; then
    PKG_MGR="dnf"
    INSTALL_CMD="dnf install -y"
elif command -v brew &>/dev/null; then
    PKG_MGR="brew"
    INSTALL_CMD="brew install"
elif command -v pacman &>/dev/null; then
    PKG_MGR="pacman"
    INSTALL_CMD="pacman -S --noconfirm"
fi

# ── Check dependencies ──
check_python() {
    local py=""
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            local ver
            ver=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
            if [[ "$(echo -e "$ver\n$PYTHON_MIN" | sort -V | head -1)" == "$PYTHON_MIN" ]] || [[ "$ver" > "$PYTHON_MIN" ]]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

check_node() {
    if command -v node &>/dev/null; then
        local ver
        ver=$(node --version 2>&1 | grep -oP '\d+' | head -1)
        if [[ "$ver" -ge "$NODE_MIN_MAJOR" ]]; then
            return 0
        fi
    fi
    return 1
}

check_bun() {
    command -v bun &>/dev/null
}

check_gum() {
    command -v gum &>/dev/null
}

# ── Install dependencies ──
install_system_deps() {
    [[ -z "$PKG_MGR" ]] && { warn "Aucun gestionnaire de paquets détecté"; return 1; }
    log "Installation des dépendances système..."
    case "$PKG_MGR" in
        apt)
            sudo apt-get update -qq || true
            sudo $INSTALL_CMD python3 python3-pip python3-venv git curl 2>/dev/null || true
            ;;
        dnf)
            sudo $INSTALL_CMD python3 python3-pip git curl 2>/dev/null || true
            ;;
        brew)
            $INSTALL_CMD python@3.12 git curl 2>/dev/null || true
            ;;
        pacman)
            sudo $INSTALL_CMD python python-pip git curl 2>/dev/null || true
            ;;
    esac
}

install_gum() {
    if check_gum; then return 0; fi
    log "Installation de gum (UI interactive)..."
    case "$OS" in
        linux)
            local gum_arch="amd64"
            [[ "$ARCH" == "aarch64" ]] && gum_arch="arm64"
            local tmp
            tmp=$(mktemp -d)
            curl -fsSL "https://github.com/charmbracelet/gum/releases/download/v0.17.0/gum_0.17.0_linux_${gum_arch}.tar.gz" -o "$tmp/gum.tar.gz"
            tar -xzf "$tmp/gum.tar.gz" -C "$tmp"
            sudo mv "$tmp/gum_0.17.0_linux_${gum_arch}/gum" /usr/local/bin/gum 2>/dev/null || {
                mkdir -p "$HOME/.local/bin"
                mv "$tmp/gum_0.17.0_linux_${gum_arch}/gum" "$HOME/.local/bin/gum"
            }
            rm -rf "$tmp"
            ;;
        macos)
            brew install gum 2>/dev/null || true
            ;;
    esac
}

# ── Main installation ──
main() {
    header

    # Step 1: System check
    log "Vérification du système..."
    log "  OS: $OS ($ARCH)"

    local py
    py=$(check_python) || true
    if [[ -n "$py" ]]; then
        ok "Python $($py --version 2>&1 | cut -d' ' -f2)"
    else
        warn "Python $PYTHON_MIN+ requis"
        install_system_deps
        py=$(check_python) || { err "Impossible d'installer Python"; exit 1; }
        ok "Python $($py --version 2>&1 | cut -d' ' -f2) installé"
    fi

    # Step 2: Install gum for TUI
    if [[ "$NO_PROMPT" -eq 0 ]]; then
        install_gum
    fi

    # Step 3: Clone / update CIEL
    local ciel_dir="$HOME/ciel"
    local repo_url="https://github.com/manas-ciel/ciel.git"

    if [[ -d "$ciel_dir/.git" ]]; then
        log "Mise à jour de CIEL..."
        cd "$ciel_dir"
        git pull --ff-only 2>/dev/null || warn "Impossible de mettre à jour"
    else
        log "Téléchargement de CIEL..."
        if command -v git &>/dev/null; then
            git clone --depth 1 "$repo_url" "$ciel_dir" 2>/dev/null || {
                warn "Git clone échoué, téléchargement ZIP..."
                mkdir -p "$ciel_dir"
                curl -fsSL "https://github.com/manas-ciel/ciel/archive/main.tar.gz" | tar -xz --strip=1 -C "$ciel_dir"
            }
        else
            mkdir -p "$ciel_dir"
            curl -fsSL "https://github.com/manas-ciel/ciel/archive/main.tar.gz" | tar -xz --strip=1 -C "$ciel_dir"
        fi
        ok "CIEL téléchargé"
    fi

    cd "$ciel_dir"

    # Step 4: Create venv
    if [[ ! -d ".venv" ]]; then
        log "Création de l'environnement virtuel..."
        $py -m venv .venv
        ok "Environnement virtuel créé"
    fi
    source .venv/bin/activate

    # Step 5: Install Python deps
    log "Installation des dépendances Python..."
    pip install --quiet --upgrade pip 2>/dev/null || true

    case "$INSTALL_MODE" in
        minimal)
            pip install -e . 2>&1 | tail -1 || warn "Échec pip install"
            ;;
        dev)
            pip install -e ".[dev]" 2>&1 | tail -1 || warn "Échec pip install dev"
            ;;
        *)
            pip install -e ".[all]" 2>&1 | tail -1 || warn "Échec pip install all"
            ;;
    esac
    ok "Dépendances installées"

    # Step 6: Config
    log "Génération de la configuration..."
    mkdir -p "$CIEL_HOME"
    if [[ ! -f "$CIEL_HOME/ciel.json" ]]; then
        cat > "$CIEL_HOME/ciel.json" <<CONF
{
  "api": { "host": "0.0.0.0", "port": $API_PORT, "log_level": "INFO" },
  "brain": {
    "modules_autoload": true,
    "default_provider": "$LLM_PROVIDER",
    "default_model": "$LLM_MODEL"
  },
  "database": { "path": "$CIEL_HOME/ciel.db" },
  "providers": {}
}
CONF
        ok "Configuration créée: $CIEL_HOME/ciel.json"
    else
        ok "Configuration existante"
    fi

    # Step 7: Identity
    if command -v ciel &>/dev/null; then
        ciel identity --create 2>/dev/null || warn "Identité déjà existante"
    fi

    # Step 8: Auto-start
    if [[ "$AUTO_START" -eq 1 ]]; then
        log "Installation du redémarrage automatique..."
        if [[ "$OS" == "linux" ]]; then
            local svc_dir="$HOME/.config/systemd/user"
            mkdir -p "$svc_dir"
            cat > "$svc_dir/ciel.service" <<SVC
[Unit]
Description=CIEL v∞.8 — Cognitive Engine
After=network-online.target

[Service]
Type=simple
ExecStart=$ciel_dir/.venv/bin/ciel-api --host 0.0.0.0 --port $API_PORT
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
SVC
            systemctl --user daemon-reload 2>/dev/null || true
            systemctl --user enable ciel 2>/dev/null || true
            systemctl --user start ciel 2>/dev/null || true
            ok "Auto-start systemd installé"
        elif [[ "$OS" == "macos" ]]; then
            local plist="$HOME/Library/LaunchAgents/com.ciel.server.plist"
            mkdir -p "$(dirname "$plist")"
            cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.ciel.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>$ciel_dir/.venv/bin/ciel-api</string>
        <string>--host</string><string>0.0.0.0</string>
        <string>--port</string><string>$API_PORT</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
</dict>
</plist>
PLIST
            launchctl load "$plist" 2>/dev/null || true
            ok "Auto-start launchd installé"
        fi
    fi

    # Step 9: Doctor
    if command -v ciel &>/dev/null; then
        ciel doctor 2>&1 | tail -5 || true
    fi

    # ── Done ──
    printf "\n${GREEN}╔══════════════════════════════════════╗${NC}\n"
    printf "${GREEN}║     ✓ Installation terminée !        ║${NC}\n"
    printf "${GREEN}╚══════════════════════════════════════╝${NC}\n\n"
    echo -e "  ${BOLD}Commandes:${NC}"
    echo -e "    ${CYAN}ciel${NC}            — Lancer le chat"
    echo -e "    ${CYAN}ciel-api${NC}        — Démarrer le serveur web (port ${API_PORT})"
    echo -e "    ${CYAN}ciel doctor${NC}     — Diagnostiquer l'installation"
    echo -e "    ${CYAN}ciel install run${NC}— Assistant d'installation complet"
    echo -e "    ${CYAN}ciel serve${NC}      — Lancer le serveur API"
    echo -e "\n  ${DIM}Ouvrir http://localhost:${API_PORT} dans le navigateur${NC}"
    echo
}

main "$@"
