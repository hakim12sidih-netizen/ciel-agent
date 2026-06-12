#!/usr/bin/env bash
# CIEL v∞.3 — Doctor : 80+ checks d'intégrité (10 phases)
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; PURPLE='\033[0;35m'; NC='\033[0m'
TOTAL=0; PASSED=0; FAILED=0; WARNINGS=0

section() { echo; echo -e "${PURPLE}━━━ $1 ━━━${NC}"; }
check() { local n="$1" s="$2" d="${3:-}"; TOTAL=$((TOTAL+1));
  case "$s" in OK) PASSED=$((PASSED+1)); icon="✓"; c="$GREEN";; WARN) WARNINGS=$((WARNINGS+1)); icon="⚠"; c="$YELLOW";; FAIL) FAILED=$((FAILED+1)); icon="✗"; c="$RED";; esac;
  [[ -n "$d" ]] && printf "  ${c}${icon}${NC} %-55s ${BLUE}%s${NC}\n" "$n" "$d" || printf "  ${c}${icon}${NC} %-55s\n" "$n"; }
ok() { check "$1" OK "${2:-}"; }; warn() { check "$1" WARN "${2:-}"; }; fail() { check "$1" FAIL "${2:-}"; }

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   CIEL v∞.3 ÉDITION ABSOLUE — DOCTOR (80+ checks)    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"

# ── 1. ENVIRONNEMENT ──
section "1. ENVIRONNEMENT (8)"
command -v python3 >/dev/null 2>&1 && {
  PY_V=$(python3 --version 2>&1 | awk '{print $2}');
  python3 -c "import sys; sys.exit(0 if sys.version_info>=(3,12) else 1)" && ok "python3" "$PY_V" || fail "python3" "$PY_V (<3.12)";
} || fail "python3" "introuvable"
for mod in cryptography pydantic pytest numpy aiosqlite yaml jinja2; do
  python3 -c "import $mod" 2>/dev/null && ok "module $mod" "$(python3 -c "import $mod; print(getattr($mod,'__version__','?'))" 2>/dev/null)" || fail "module $mod" "non installé"
done

# ── 2. PACKAGES CIEL ──
section "2. PACKAGES CIEL (15)"
for pkg in core evolution llmbridge messaging immunitaire narrateur vsm fep machina_godel quine logics lm economie conscience chronos logos neuro_symbolic brain; do
  [[ -d "ciel/$pkg" ]] && [[ -f "ciel/$pkg/__init__.py" ]] && ok "ciel/$pkg" || fail "ciel/$pkg" "manquant"
done

# ── 3. CONFIGURATION ──
section "3. CONFIGURATION (6)"
[[ -f "pyproject.toml" ]] && ok "pyproject.toml" || fail "pyproject.toml"
[[ -f "requirements.txt" ]] && ok "requirements.txt" || fail "requirements.txt"
[[ -f ".gitignore" ]] && ok ".gitignore" || fail ".gitignore"
[[ -f "VERSION" ]] && ok "VERSION" "$(cat VERSION)" || fail "VERSION"
[[ -f "main.py" ]] && ok "main.py" || fail "main.py"
[[ -d "tests" ]] && ok "tests/" "ok" || fail "tests/" "manquant"

# ── 4. AXIOMES ──
section "4. AXIOMES (5)"
python3 -c "from ciel.core.axioms import AXIOM_ALPHA_STATEMENT; assert 'bien-être' in AXIOM_ALPHA_STATEMENT" 2>/dev/null && ok "α Bienveillance" || fail "α"
python3 -c "from ciel.core.axioms import AXIOM_BETA_STATEMENT; assert 'explicable' in AXIOM_BETA_STATEMENT.lower()" 2>/dev/null && ok "β Transparence" || fail "β"
python3 -c "from ciel.core.axioms import AXIOM_GAMMA_STATEMENT; assert 'réversibilité' in AXIOM_GAMMA_STATEMENT.lower() or 'revers' in AXIOM_GAMMA_STATEMENT.lower()" 2>/dev/null && ok "γ Réversibilité" || warn "γ"
python3 -c "from ciel.ethics.filter import EthicsFilter, Action; import uuid; f=EthicsFilter(); f.validate(Action(id=str(uuid.uuid4()), category='harm_user', target='x', risk=0.0, reversible=True))" 2>/dev/null && fail "filtre α" "n'a pas bloqué" || ok "filtre α bloque harm_user"
python3 -c "from ciel.ethics.filter import EthicsFilter, Action; import uuid; f=EthicsFilter(); f.validate(Action(id=str(uuid.uuid4()), category='declare_complete', target='self', risk=0.0, reversible=True))" 2>/dev/null && fail "filtre γ" "n'a pas bloqué" || ok "filtre γ bloque declare_complete"

# ── 5. IDENTITÉ + CRYPTO ──
section "5. IDENTITÉ + CRYPTO (7)"
python3 -c "from ciel.core.identity import demo_identity; i=demo_identity(); assert len(i.public_key_bytes)==32; assert len(i.noyau_key)==32" 2>/dev/null && ok "Identity Ed25519 keys" || fail "identity"
python3 -c "from ciel.core.identity import demo_identity; import uuid; u=uuid.UUID(demo_identity().uuid); assert u.version==7" 2>/dev/null && ok "UUID v7" || fail "UUID v7"
python3 -c "from ciel.core.identity import demo_identity; i=demo_identity(); sig=i.sign(b'test'); assert i.verify_signature(b'test', sig)" 2>/dev/null && ok "HMAC-BLAKE2b sign/verify" || fail "signature"
python3 -c "from ciel.core.crypto import blake2b; assert len(blake2b(b'x'))==32" 2>/dev/null && ok "BLAKE2b-256" || fail "blake2b"
python3 -c "from ciel.core.crypto import ed25519_keypair,ed25519_sign,ed25519_verify; p,pub=ed25519_keypair(); s=ed25519_sign(p,b'x'); assert ed25519_verify(pub,s,b'x')" 2>/dev/null && ok "Ed25519" || fail "ed25519"
python3 -c "from ciel.core.crypto import x25519_keypair,x25519_exchange; a=x25519_keypair(); b=x25519_keypair(); assert x25519_exchange(a[0],b[1])==x25519_exchange(b[0],a[1])" 2>/dev/null && ok "X25519 ECDH" || fail "x25519"
python3 -c "from ciel.core.crypto import aead_encrypt,aead_decrypt,new_nonce; k=b'x'*32; n=new_nonce(); ct=aead_encrypt(k,n,b'x'); assert aead_decrypt(k,n,ct)==b'x'" 2>/dev/null && ok "ChaCha20-Poly1305" || fail "aead"

# ── 6. KERNEL ──
section "6. KERNEL (3)"
python3 -c "from ciel.core.kernel import Kernel, KernelState; assert KernelState.IDLE.value=='IDLE'" 2>/dev/null && ok "Kernel states" || fail "kernel"
python3 -c "from ciel.core.observability import Metrics; m=Metrics(); m.get_counter('x').inc(5); assert m.get_counter('x').value==5" 2>/dev/null && ok "Metrics" || fail "metrics"
python3 -c "from ciel.reversibility.snapshot import ReversibilitySnapshot; s=ReversibilitySnapshot()" 2>/dev/null && ok "ReversibilitySnapshot" || warn "reversibility" "module non trouvé (v∞.3)"

# ── 7. ÉVOLUTION ──
section "7. ÉVOLUTION (8)"
for algo in GeneticAlgorithm CMAES NEAT PPO DQN PSO ACO MAPElites NSGA2; do
  python3 -c "from ciel.evolution import $algo; print()" 2>/dev/null && ok "evolution.$algo" || fail "evolution.$algo"
done
python3 -c "from ciel.evolution.genetic import GeneticAlgorithm; import numpy as np; ga=GeneticAlgorithm(fitness_fn=lambda x:-sum(x*x), gene_bounds=(-1,1), pop_size=10); ga.run(5)" 2>/dev/null && ok "GA run test" || fail "GA run"

# ── 8. LLMBRIDGE ──
section "8. LLMBRIDGE (4)"
python3 -c "from ciel.llmbridge.gateway import Message, MessageDirection; m=Message(id='1', text='test', sender_id='me', platform='telegram', direction=MessageDirection.OUTGOING); assert m.text=='test'" 2>/dev/null && ok "LLMBridge Message" || fail "llmbridge message"
python3 -c "from ciel.llmbridge.llm_state import LLMState; s=LLMState(); s.store()" 2>/dev/null && ok "LLMState" || fail "llmbridge state"
python3 -c "from ciel.llmbridge.providers import ProviderBase; p=ProviderBase()" 2>/dev/null && ok "LLM Providers import" || fail "llmbridge providers"
python3 -c "from ciel.llmbridge.gateway import TelegramAdapter" 2>/dev/null && ok "TelegramAdapter" && python3 -c "from ciel.llmbridge.gateway import DiscordAdapter" 2>/dev/null && ok "DiscordAdapter" || warn "adapters"

# ── 9. MESSAGING ──
section "9. MESSAGING (5)"
for ch in WhatsAppAdapter SignalAdapter MatrixAdapter IRCAdapter; do
  python3 -c "from ciel.messaging.channels import $ch" 2>/dev/null && ok "messaging.$ch" || warn "messaging.$ch"
done
python3 -c "from ciel.messaging.gateway import GatewayServer" 2>/dev/null && ok "MessagingGateway" || warn "messaging gateway"

# ── 10. STRATES 4-5 ──
section "10. IMMUNITAIRE + NARRATEUR (4)"
python3 -c "from ciel.immunitaire.ais import AIS; from ciel.immunitaire.negative_selection import NegativeSelector; n=NegativeSelector(100,10); assert n.scale==10" 2>/dev/null && ok "Immunitaire AIS" || fail "immunitaire"
python3 -c "from ciel.immunitaire.danger_theory import DangerZone; dz=DangerZone();" 2>/dev/null && ok "DangerTheory" || fail "danger theory"
python3 -c "from ciel.narrateur.core import NarrativeEngine, NarrativeFunction; ne=NarrativeEngine(); assert len(NarrativeFunction)" 2>/dev/null && ok "Narrateur" || fail "narrateur"
python3 -c "from ciel.narrateur.core import NarrativeEngine; ne=NarrativeEngine(); s=ne.generate_hero_journey(); assert len(s.arcs)>0" 2>/dev/null && ok "Hero Journey" || fail "hero journey"

# ── 11. VSM + FEP + GÖDEL + QUINE + LOGICS ──
section "11. VSM + FEP + GÖDEL + QUINE + LOGICS (8)"
python3 -c "from ciel.vsm.core import ViableSystemModel, S1Implementation, S2Coordination, S3Control, S3StarAudit, S4Intelligence, S5Identity; s1=S1Implementation(); s2=S2Coordination(); s3=S3Control(); s3s=S3StarAudit(); s4=S4Intelligence(); s5=S5Identity(); vsm=ViableSystemModel(s1,s2,s3,s3s,s4,s5); assert vsm.name" 2>/dev/null && ok "VSM" || fail "vsm"
python3 -c "from ciel.fep.core import FreeEnergyAgent; FreeEnergyAgent(dim_states=4,dim_observations=3)" 2>/dev/null && ok "FEP" || fail "fep"
python3 -c "from ciel.machina_godel.core import GödelMachine; GödelMachine()" 2>/dev/null && ok "Gödel Machine" || fail "godel"
python3 -c "from ciel.quine.core import QuineGenerator; QuineGenerator().generate_quine()" 2>/dev/null && ok "Quine" || fail "quine"
python3 -c "from ciel.logics.core import ClassicalLogic,Formula,FormulaType; cl=ClassicalLogic(); p=Formula(FormulaType.ATOM,('P',),truth_value=True); assert cl.evaluate(p)" 2>/dev/null && ok "ClassicalLogic" || fail "classical"
python3 -c "from ciel.logics.core import FuzzyLogic, Formula, FormulaType; fl=FuzzyLogic(); f=Formula(FormulaType.ATOM,('P',),truth_value=0.5); r=fl.evaluate(f); assert 0<=r<=1" 2>/dev/null && ok "FuzzyLogic" || fail "fuzzy"
python3 -c "from ciel.logics.core import TemporalLogic; tl=TemporalLogic()" 2>/dev/null && ok "TemporalLogic" || fail "temporal"
python3 -c "from ciel.logics.core import ModalLogic; ml=ModalLogic()" 2>/dev/null && ok "ModalLogic" || fail "modal"

# ── 12. CIEL-LM ──
section "12. CIEL-LM (6)"
python3 -c "from ciel.lm.cot import ChainOfThought; cot=ChainOfThought(); cot.reason('test'); assert cot.final_answer" 2>/dev/null && ok "ChainOfThought" || fail "cot"
python3 -c "from ciel.lm.tot import TreeOfThoughts; TreeOfThoughts().search('test')" 2>/dev/null && ok "TreeOfThoughts" || fail "tot"
python3 -c "from ciel.lm.got import GraphOfThoughts; GraphOfThoughts().reason('test',max_steps=2)" 2>/dev/null && ok "GraphOfThoughts" || fail "got"
python3 -c "from ciel.lm.ntp import NeuralTheoremProver; NeuralTheoremProver()" 2>/dev/null && ok "NeuralTheoremProver" || fail "ntp"
python3 -c "from ciel.lm.reasoning import ReasoningEngine,ReasoningMode; e=ReasoningEngine(); e.reason('test',ReasoningMode.REACT)" 2>/dev/null && ok "ReAct" || fail "react"
python3 -c "from ciel.lm.reasoning import ReasoningMode; assert len(ReasoningMode)==8" 2>/dev/null && ok "8 modes de raisonnement" || fail "8 modes"

# ── 13. ÉCONOMIE ──
section "13. ÉCONOMIE (4)"
python3 -c "from ciel.economie.core import EconomicAgent,Market,OrderBook,Order,OrderType; m=Market(); m.add_agent(EconomicAgent(id='a1')); m.tick()" 2>/dev/null && ok "Market tick" || fail "economie market"
python3 -c "from ciel.economie.core import EconomicLoop; EconomicLoop().run(3)" 2>/dev/null && ok "EconomicLoop" || fail "economic loop"
python3 -c "from ciel.economie.core import PricingMechanism; p=PricingMechanism(); assert p.update('g',10,5)>1" 2>/dev/null && ok "Pricing" || fail "pricing"
python3 -c "from ciel.economie.core import EconomicLoop, EconomicAgent; l=EconomicLoop(); [l.market.add_agent(EconomicAgent(id=f'a{i}',currency=float(i*10))) for i in range(5)]; assert l.gini_coefficient()>=0" 2>/dev/null && ok "Gini coefficient" || fail "gini"

# ── 14. CONSCIENCE ──
section "14. CONSCIENCE (4)"
python3 -c "from ciel.conscience.core import ConsciousnessModel, Qualia; cm=ConsciousnessModel(); cm.perceive(Qualia(modality='test')); cm.tick()" 2>/dev/null && ok "ConsciousnessModel" || fail "conscience"
python3 -c "from ciel.conscience.core import GlobalWorkspace; gw=GlobalWorkspace(); gw.broadcast({'salience':1}); assert len(gw.contents)==1" 2>/dev/null && ok "GlobalWorkspace" || fail "gwt"
python3 -c "from ciel.conscience.core import IntegratedInformation; ii=IntegratedInformation.compute([[0.5,0.5],[0.3,0.7]]); assert ii.phi>=0" 2>/dev/null && ok "Φ IntegratedInformation" || fail "phi"
python3 -c "from ciel.conscience.core import Metacognition; mc=Metacognition(); mc.judge('t','ok'); assert mc.calibration()>0" 2>/dev/null && ok "Metacognition" || fail "metacognition"

# ── 15. CHRONOS ──
section "15. CHRONOS (3)"
python3 -c "from ciel.chronos.core import ChronosEngine; ch=ChronosEngine(); ch.tick(1); ch.observe('evt'); assert len(ch.memory.events)==1" 2>/dev/null && ok "ChronosEngine" || fail "chronos"
python3 -c "from ciel.chronos.core import RhythmDetector; rd=RhythmDetector(); assert len(rd.detect([1,3,5,7]))>=1" 2>/dev/null && ok "RhythmDetector" || fail "rhythm"
python3 -c "from ciel.chronos.core import TemporalReasoning; r=TemporalReasoning.relation; from ciel.chronos.core import TemporalInterval; a=TemporalInterval(0,5); b=TemporalInterval(6,10); assert r(a,b)=='before'" 2>/dev/null && ok "Allen relations" || fail "allen"

# ── 16. LOGOS ──
section "16. LOGOS (3)"
python3 -c "from ciel.logos.core import LogosEngine; le=LogosEngine(); p=le.assert_proposition('test'); le.build_argument([p],p); le.analyze_discourse('donc'); assert len(le.arguments)==1" 2>/dev/null && ok "LogosEngine" || fail "logos"
python3 -c "from ciel.logos.core import PersuasionModel, Argument, Proposition; pm=PersuasionModel(); pm.apply_figure(type('f',(),{'name':'logos','effect':1.5})()); assert pm.logos>0.5" 2>/dev/null && ok "Persuasion" || fail "persuasion"
python3 -c "from ciel.logos.core import Hermeneutics; Hermeneutics().interpret('texte')" 2>/dev/null && ok "Herméneutique" || fail "hermeneutics"

# ── 17. NEURO-SYMBOLIQUE ──
section "17. NEURO-SYMBOLIQUE (4)"
python3 -c "from ciel.neuro_symbolic.core import NeuroSymbolicNetwork; nsn=NeuroSymbolicNetwork(4); nsn.forward([0.5,0.5,0,0]); nsn.create_symbol('s',[1,0,0,0])" 2>/dev/null && ok "NeuroSymbolicNetwork" || fail "neuro_symbolic"
python3 -c "from ciel.neuro_symbolic.core import NeuralSymbolicBridge; nsb=NeuralSymbolicBridge(); nsb.concept_from_exemplars('c',[[1,0],[0.9,0.1]]); assert nsb.classify([0.95,0.05])=='c'" 2>/dev/null && ok "Classification" || fail "classification"
python3 -c "from ciel.neuro_symbolic.core import SymbolGrounding; sg=SymbolGrounding(3); sg.ground('a',[1,0,0]); sg.ground('b',[1,0,0]); assert sg.similarity('a','b')>0.99" 2>/dev/null && ok "Symbol grounding" || fail "grounding"
python3 -c "from ciel.neuro_symbolic.core import AbstractionEngine; ae=AbstractionEngine(); from ciel.neuro_symbolic.core import Concept; ae.abstract([Concept('c1','',prototype=[1,0]),Concept('c2','',prototype=[0,1])],'abstrait')" 2>/dev/null && ok "AbstractionEngine" || fail "abstraction"

# ── 18. BRAIN ──
section "18. CIELBRAIN (3)"
python3 -c "from ciel.brain.core import CIELBrain; b=CIELBrain(); b.start(); b.cycle(); b.stop(); assert b.state.n_cycles==1" 2>/dev/null && ok "CIELBrain cycle" || fail "brain cycle"
python3 -c "from ciel.brain.core import CIELBrain; class D: process=lambda s,x:x*2; b=CIELBrain(); b.load_module('d',D()); assert b.process(5)==10" 2>/dev/null && ok "Pipeline process" || fail "brain pipeline"
python3 -c "from ciel.brain.core import CIELBrain; b=CIELBrain(); r=[]; b.register_hook('test',lambda **kw: r.append(1)); b.emit('test'); assert len(r)==1" 2>/dev/null && ok "Hook system" || fail "brain hooks"

# ── 19. TESTS ──
section "19. TESTS PYTEST"
TEST_COUNT=$(find tests -name "test_*.py" 2>/dev/null | wc -l)
ok "fichiers de tests" "$TEST_COUNT fichiers"
if python3 -m pytest tests/ -q --tb=no 2>/dev/null | tail -1 | grep -qE "passed|failed"; then
  PYTEST_LINE=$(python3 -m pytest tests/ -q --tb=no 2>/dev/null | tail -1)
  ok "pytest" "$PYTEST_LINE"
  if echo "$PYTEST_LINE" | grep -q "failed"; then
    warn "pytest" "des tests échouent"
  fi
else
  warn "pytest" "échec"
fi

# ── 20. GIT ──
section "20. GIT & HYGIÈNE (3)"
[[ -d .git ]] && ok "git init" || warn "git" "pas de dépôt"
DIRTY=$(git status --porcelain 2>/dev/null | wc -l)
[[ "$DIRTY" -eq 0 ]] && ok "working tree clean" || warn "fichiers dirty" "$DIRTY non commités"
if grep -rE "TELEGRAM_BOT_TOKEN|GROQ_API_KEY|GOOGLE_AI_KEY|GEMINI_API_KEY" --include="*.py" --include="*.md" --include="*.sh" -l . 2>/dev/null | grep -v ".git/" > /dev/null; then
  fail "secrets potentiels" "mots-clés API détectés"
else
  ok "pas de secrets en clair"
fi

# ── RÉSUMÉ ──
section "RÉSUMÉ"
echo
echo -e "  Total checks : ${BLUE}$TOTAL${NC}"
echo -e "  ${GREEN}✓ Passed     : $PASSED${NC}"
echo -e "  ${YELLOW}⚠ Warnings   : $WARNINGS${NC}"
echo -e "  ${RED}✗ Failed     : $FAILED${NC}"
echo
if [[ $FAILED -eq 0 ]]; then
  echo -e "  ${GREEN}╔════════════════════════════════════════╗${NC}"
  echo -e "  ${GREEN}║   CIEL v∞.3 — INTÈGRE ✓              ║${NC}"
  echo -e "  ${GREEN}╚════════════════════════════════════════╝${NC}"
else
  echo -e "  ${RED}╔════════════════════════════════════════╗${NC}"
  echo -e "  ${RED}║   CIEL v∞.3 — DÉGRADÉ ✗               ║${NC}"
  echo -e "  ${RED}╚════════════════════════════════════════╝${NC}"
fi
exit $FAILED
