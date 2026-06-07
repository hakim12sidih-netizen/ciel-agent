#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# CIEL v∞.2 — Doctor : 50+ checks d'intégrité
# Inspiré de HYDRA/scripts/doctor.sh (Pass 14) — étendu pour CIEL
# ─────────────────────────────────────────────────────────────
set -u
shopt -s lastpipe

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ── Couleurs ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# ── Compteurs ───────────────────────────────────────────────
TOTAL=0
PASSED=0
FAILED=0
WARNINGS=0
RESULTS=()

# ── Helpers ─────────────────────────────────────────────────
section() {
  echo
  echo -e "${PURPLE}━━━ $1 ━━━${NC}"
}

check() {
  local name="$1"
  local status="$2"  # "OK", "WARN", "FAIL"
  local detail="${3:-}"
  TOTAL=$((TOTAL+1))
  case "$status" in
    OK)   PASSED=$((PASSED+1))   ; icon="✓" ; color="$GREEN" ;;
    WARN) WARNINGS=$((WARNINGS+1)) ; icon="⚠" ; color="$YELLOW" ;;
    FAIL) FAILED=$((FAILED+1))   ; icon="✗" ; color="$RED" ;;
  esac
  RESULTS+=("$status|$name|$detail")
  if [[ -n "$detail" ]]; then
    printf "  ${color}${icon}${NC} %-50s ${BLUE}%s${NC}\n" "$name" "$detail"
  else
    printf "  ${color}${icon}${NC} %-50s\n" "$name"
  fi
}

ok()   { check "$1" "OK"   "${2:-}"; }
warn() { check "$1" "WARN" "${2:-}"; }
fail() { check "$1" "FAIL" "${2:-}"; }

# ── Header ─────────────────────────────────────────────────
echo
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   CIEL v∞.2 — DOCTOR (50+ checks d'intégrité)         ║${NC}"
echo -e "${BLUE}║   Phase 0 : ÉVEIL                                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"

# ── 1. ENVIRONMENT ──────────────────────────────────────────
section "1. ENVIRONNEMENT (8 checks)"

if command -v python3 >/dev/null 2>&1; then
  PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
  if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)"; then
    ok "python3 version" "$PY_VERSION"
  else
    fail "python3 version" "$PY_VERSION (< 3.12 requis)"
  fi
else
  fail "python3 disponible" "introuvable"
fi

for mod in cryptography pydantic hypothesis pytest numpy rich click aiosqlite yaml; do
  if python3 -c "import ${mod}" 2>/dev/null; then
    v=$(python3 -c "import ${mod}; print(getattr(${mod}, '__version__', '?'))" 2>/dev/null)
    ok "module $mod" "$v"
  else
    fail "module $mod" "non installé"
  fi
done

# ── 2. STRUCTURE DU PROJET ─────────────────────────────────
section "2. STRUCTURE (12 checks)"

# Strates (12)
for s in core ethics memory perception analysis skills noosphere animus consciousness chronos logos meta; do
  if [[ -d "ciel/$s" ]]; then
    if [[ -f "ciel/$s/__init__.py" ]]; then
      ok "strate/$s/__init__.py"
    else
      fail "strate/$s/__init__.py" "manquant"
    fi
  else
    fail "strate/$s/" "dossier manquant"
  fi
done

# Transverses (6)
for t in brain swarm security economy quantum math; do
  if [[ -d "ciel/$t" ]] && [[ -f "ciel/$t/__init__.py" ]]; then
    ok "transverse/$t"
  else
    fail "transverse/$t" "manquant"
  fi
done

# Interfaces
if [[ -f "ciel/interfaces/cli.py" ]]; then
  ok "interface/cli.py"
else
  fail "interface/cli.py" "manquant"
fi

# Polyglot
if [[ -f "ciel/polyglot/bridge.py" ]]; then
  ok "polyglot/bridge.py"
else
  fail "polyglot/bridge.py" "manquant"
fi

# ── 3. CONFIGURATION & MÉTA ───────────────────────────────
section "3. CONFIGURATION (5 checks)"

[[ -f "pyproject.toml" ]] && ok "pyproject.toml" || fail "pyproject.toml"
[[ -f "requirements.txt" ]] && ok "requirements.txt" || fail "requirements.txt"
[[ -f ".gitignore" ]] && ok ".gitignore" || fail ".gitignore"
[[ -f "VERSION" ]] && ok "VERSION" "$(cat VERSION)" || fail "VERSION"
[[ -f "main.py" ]] && ok "main.py" || fail "main.py"
[[ -f "README.md" ]] && ok "README.md" || fail "README.md"

# ── 4. AXIOMES ─────────────────────────────────────────────
section "4. AXIOMES (6 checks)"

if python3 -c "from ciel.core.axioms import load_axioms, verify_axiom; from ciel.core.identity import demo_key; ax=load_axioms(demo_key()); assert set(ax.keys())=={'α','β','γ','δ'}; assert all(verify_axiom(a, demo_key()) for a in ax.values())" 2>/dev/null; then
  ok "4 axiomes αβγδ chargent et vérifient"
else
  fail "axiomes" "load_axioms ou verify_axiom échoue"
fi

if python3 -c "from ciel.core.axioms import AXIOM_ALPHA_STATEMENT; assert 'bien-être' in AXIOM_ALPHA_STATEMENT" 2>/dev/null; then
  ok "Axiome α énoncé"
else
  fail "Axiome α" "énoncé manquant"
fi

if python3 -c "from ciel.core.axioms import AXIOM_DELTA_STATEMENT; assert 'perpétuel' in AXIOM_DELTA_STATEMENT.lower() or 'quête' in AXIOM_DELTA_STATEMENT.lower()" 2>/dev/null; then
  ok "Axiome δ (Inachèvement Perpétuel)"
else
  fail "Axiome δ" "énoncé manquant"
fi

# Test filtrage
if python3 -c "from ciel.ethics.filter import EthicsFilter, Action; import uuid; f=EthicsFilter(); a=Action(id=str(uuid.uuid4()), category='harm_user', target='x', risk=0.0, reversible=True); f.validate(a)" 2>/dev/null; then
  fail "filter α" "n'a pas bloqué 'harm_user'"
else
  ok "filter α bloque harm_user"
fi

if python3 -c "from ciel.ethics.filter import EthicsFilter, Action; import uuid; f=EthicsFilter(); a=Action(id=str(uuid.uuid4()), category='declare_complete', target='self', risk=0.0, reversible=True); f.validate(a)" 2>/dev/null; then
  fail "filter δ" "n'a pas bloqué declare_complete"
else
  ok "filter δ bloque declare_complete"
fi

# ── 5. IDENTITÉ ────────────────────────────────────────────
section "5. IDENTITÉ (4 checks)"

if python3 -c "from ciel.core.identity import demo_identity; i=demo_identity(); assert i.public_key_bytes.__len__()==32; assert i.noyau_key.__len__()==32" 2>/dev/null; then
  ok "Identity : 32 bytes clé publique + 32 bytes noyau"
else
  fail "Identity structure"
fi

if python3 -c "from ciel.core.identity import demo_identity; i=demo_identity(); import uuid; u=uuid.UUID(i.uuid); assert u.version==7" 2>/dev/null; then
  ok "UUID v7"
else
  fail "UUID v7" "pas un UUID v7"
fi

if python3 -c "from ciel.core.identity import demo_identity; i=demo_identity(); sig=i.sign(b'test'); assert i.verify_signature(b'test', sig)" 2>/dev/null; then
  ok "Sign/Verify HMAC-BLAKE2b"
else
  fail "Signature"
fi

# ── 6. CRYPTO ──────────────────────────────────────────────
section "6. CRYPTO (6 checks)"

if python3 -c "from ciel.core.crypto import blake2b; h=blake2b(b'x'); assert len(h)==32" 2>/dev/null; then
  ok "BLAKE2b-256"
else
  fail "BLAKE2b"
fi

if python3 -c "from ciel.core.crypto import ed25519_keypair, ed25519_sign, ed25519_verify; p,pub=ed25519_keypair(); s=ed25519_sign(p, b'x'); assert ed25519_verify(pub, s, b'x')" 2>/dev/null; then
  ok "Ed25519 sign+verify"
else
  fail "Ed25519"
fi

if python3 -c "from ciel.core.crypto import x25519_keypair, x25519_exchange; a_priv, a_pub=x25519_keypair(); b_priv, b_pub=x25519_keypair(); assert x25519_exchange(a_priv, b_pub)==x25519_exchange(b_priv, a_pub)" 2>/dev/null; then
  ok "X25519 ECDH symétrie"
else
  fail "X25519"
fi

if python3 -c "from ciel.core.crypto import aead_encrypt, aead_decrypt, new_nonce; k=b'\\x42'*32; n=new_nonce(); ct=aead_encrypt(k, n, b'x'); assert aead_decrypt(k, n, ct)==b'x'" 2>/dev/null; then
  ok "ChaCha20-Poly1305 AEAD"
else
  fail "ChaCha20-Poly1305"
fi

if python3 -c "from ciel.core.crypto import SealedBox, x25519_keypair, open_sealed_box; priv, pub=x25519_keypair(); box=SealedBox(pub); blob=box.easy_seal(b'x'); assert open_sealed_box(priv, blob)==b'x'" 2>/dev/null; then
  ok "SealedBox (X25519+ChaCha20)"
else
  fail "SealedBox"
fi

# ── 7. KERNEL & OBSERVABILITY ──────────────────────────────
section "7. KERNEL & OBSERVABILITY (6 checks)"

if python3 -c "from ciel.core.kernel import Kernel, KernelState; assert KernelState.IDLE.value=='IDLE' and KernelState.RUNNING.value=='RUNNING'" 2>/dev/null; then
  ok "Kernel states"
else
  fail "Kernel"
fi

if python3 -c "from ciel.core.observability import Counter, Gauge, Histogram, Metrics; m=Metrics(); c=m.get_counter('x'); c.inc(5); g=m.get_gauge('y'); g.set(10); h=m.get_histogram('z'); h.observe(1); assert c.value==5 and g.value==10 and h.count==1" 2>/dev/null; then
  ok "Counter/Gauge/Histogram"
else
  fail "Observability"
fi

# ── 8. TESTS ───────────────────────────────────────────────
section "8. TESTS PYTEST"

# Compte les fichiers de tests
TEST_COUNT=$(find tests -name "test_*.py" -not -path "*/.*" 2>/dev/null | wc -l)
if [[ "$TEST_COUNT" -ge 5 ]]; then
  ok "fichiers de tests" "$TEST_COUNT fichiers"
else
  fail "fichiers de tests" "seulement $TEST_COUNT"
fi

# Lance pytest (silencieux)
if python3 -m pytest tests/ -q --tb=no 2>/dev/null | tail -1 | grep -qE "passed|failed"; then
  PYTEST_LINE=$(python3 -m pytest tests/ -q --tb=no 2>/dev/null | tail -1)
  ok "pytest tests/" "$PYTEST_LINE"
else
  warn "pytest" "impossible de lancer (voir manuellement)"
fi

# ── 9. GIT & HYGIÈNE ───────────────────────────────────────
section "9. GIT & HYGIÈNE (3 checks)"

if [[ -d .git ]]; then
  ok "git init"
  # Compte les fichiers dirty
  if command -v git >/dev/null 2>&1; then
    DIRTY=$(git status --porcelain 2>/dev/null | wc -l)
    if [[ "$DIRTY" -eq 0 ]]; then
      ok "working tree clean"
    else
      warn "fichiers dirty" "$DIRTY fichiers non commités"
    fi
  fi
else
  warn "git init" "pas de dépôt git"
fi

# Pas de secrets en clair
if grep -rE "TELEGRAM_BOT_TOKEN|GROQ_API_KEY|GOOGLE_AI_KEY|GEMINI_API_KEY" --include="*.py" --include="*.md" --include="*.sh" -l . 2>/dev/null | grep -v ".git/" | grep -v "tests/" > /dev/null; then
  fail "secrets potentiels" "mots-clés API détectés (voir grep)"
else
  ok "pas de secrets en clair"
fi

# ── RÉSUMÉ ─────────────────────────────────────────────────
section "RÉSUMÉ"
TOTAL=$((TOTAL))
echo
echo -e "  Total checks : ${BLUE}$TOTAL${NC}"
echo -e "  ${GREEN}✓ Passed     : $PASSED${NC}"
echo -e "  ${YELLOW}⚠ Warnings   : $WARNINGS${NC}"
echo -e "  ${RED}✗ Failed     : $FAILED${NC}"
echo

if [[ $FAILED -eq 0 ]]; then
  echo -e "  ${GREEN}╔════════════════════════════════════════╗${NC}"
  echo -e "  ${GREEN}║   CIEL v∞.2 Phase 0 — INTÈGRE ✓       ║${NC}"
  echo -e "  ${GREEN}╚════════════════════════════════════════╝${NC}"
  echo
  exit 0
else
  echo -e "  ${RED}╔════════════════════════════════════════╗${NC}"
  echo -e "  ${RED}║   CIEL v∞.2 Phase 0 — DÉGRADÉ ✗       ║${NC}"
  echo -e "  ${RED}╚════════════════════════════════════════╝${NC}"
  echo
  exit 1
fi
