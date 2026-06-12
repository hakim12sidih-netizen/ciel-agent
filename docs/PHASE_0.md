# Phase 0 : ÉVEIL — Journal d'implémentation

> **Semaines 1-8** : Noyau Primordial, Axiomes signés, Infra Tier 0,
> Connecteurs Tier A, logging total, tests.

## Objectifs Phase 0

- [x] Noyau Primordial (Identity, Kernel, Observability)
- [x] 4 Axiomes αβγδ signés cryptographiquement
- [x] Crypto standard (BLAKE2b, Ed25519, X25519, ChaCha20-Poly1305)
- [x] Éthique (filter, transparency, reversibility)
- [x] 12 strates + 6 transverses (stubs alignés v∞.2)
- [x] Polyglot Bridge (subprocess wrapper)
- [x] Doctor 50+ checks
- [x] Tests property-based sur les 4 axiomes

## Statistiques Phase 0

| Métrique | Valeur |
|----------|--------|
| Modules Python | 35+ |
| Lignes de code | ~3000 |
| Tests | 100+ (property-based) |
| Doctor checks | 50+ |
| Axiomes | 4 (α,β,γ,δ) |
| Strates | 12 |
| Transverses | 6 |

## Architecture réelle

```
ciel/
├── core/                      # Strate 1 — Noyau Primordial
│   ├── axioms.py              # α,β,γ,δ signés BLAKE2b
│   ├── identity.py            # Ed25519 + UUID v7 + persistence
│   ├── crypto.py              # BLAKE2b, Ed25519, X25519, ChaCha20
│   ├── kernel.py              # boucle asyncio + tick
│   └── observability/
│       └── metrics.py         # Counter/Gauge/Histogram
├── ethics/                    # Strate 2 — Éthique
│   ├── axioms_guard.py        # exceptions α/β/γ/δ
│   ├── filter.py              # validation pre-exécution
│   ├── transparency.py        # certificates Axiome β
│   └── reversibility.py       # snapshots Axiome γ
├── memory/                    # Strate 4 (Phase 1+)
├── perception/                # Strate 5 (Phase 1+)
├── analysis/                  # Strate 6 (Phase 1+)
├── skills/                    # Strate 7 (Phase 3+)
├── noosphere/                 # Strate 8 (Phase 3+)
├── animus/                    # Strate 9 (Phase 3+)
├── consciousness/             # Strate 10 (Phase 2+)
├── chronos/                   # Strate 11 (Phase 1+)
├── logos/                     # Strate 12 (Phase 1+)
├── meta/                      # Strate 12+ (Phase 4+)
├── brain/                     # Transverse (Phase 2+)
├── swarm/                     # Transverse (Phase 4+)
├── security/                  # Strate 3 / Transverse (Phase 2+)
├── economy/                   # Transverse (Phase 4+)
├── quantum/                   # Transverse (Phase 4+)
├── math/                      # Transverse (Phase 3+)
├── interfaces/                # CLI + future TUI/voice/canvas
│   └── cli.py                 # Click-based
└── polyglot/                  # Bridge vers Rust/Go/C
    └── bridge.py              # subprocess JSON-RPC
```

## Décisions architecturales

### 1. Python 3.12+ strict

Toutes les annotations de type sont obligatoires. `mypy --strict` est
la cible (Phase 0 : pas encore activé dans CI, à venir Phase 1).

### 2. Pas de typage `Any`

Tout est typé explicitement. Si on a besoin d'un "escape hatch",
on utilise `unknown` (safer) avec un `cast()` explicite.

### 3. Immutabilité par défaut

Tous les dataclasses sont `frozen=True, slots=True`. Pas de mutation
silencieuse. Pour muter, on crée une nouvelle instance.

### 4. Cryptographie standard

- **BLAKE2b** au lieu de BLAKE3 (BLAKE3 non installé, BLAKE2b = même famille)
- **Ed25519** (signatures)
- **X25519** (échange de clés)
- **ChaCha20-Poly1305** (AEAD)
- **HKDF-SHA256** (dérivation)

### 5. Tests property-based

`hypothesis` est utilisé pour vérifier que les axiomes tiennent sur
**1000+ exemples aléatoires**. C'est plus fort que des tests unitaires
classiques car ça teste les invariants, pas des cas particuliers.

### 6. Persistence append-only

Les snapshots sont stockés en JSONL (un snapshot par ligne) :
- Append-only (jamais d'écrasement)
- Vérification de signature au chargement
- Corruption = on ignore la ligne, on continue

## Prochaines étapes — Phase 1 (CONSCIENCE)

Semaines 9-24 (3 mois) :
- Strate 4 (Mémoire) : graphe sémantique SQLite
- Strate 5 (Perception) : filesystem watcher + 1 connecteur Tier A
- Strate 6 (Analyse) : 3 modes (descriptif, diagnostique, prédictif)
- Strate 11 (Chronos) : scheduler asyncio + sommeil
- Strate 12 (Logos) : interface LLM (Ollama local)
- Absorption HYDRA, Hermes-Agent, OpenClaw : modules migrés vers CIEL natif

Cible Phase 1 : 500+ tests, doctor 100+ checks.
