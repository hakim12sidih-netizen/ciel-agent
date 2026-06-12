# Architecture CIEL v∞.2

> **Édition Singularité — 21 parties + 5 annexes**
>
> Cette documentation reflète l'architecture cible. L'implémentation
> est progressive (Phase 0 → Phase ∞).

## Sommaire

1. [Vue d'ensemble des 12 strates + 6 transverses](01_vue_ensemble.md)
2. [Détail des 12 strates cognitives](02_12_strates.md)
3. [Cerveau neurobiologique + Swarm](03_brain_swarm.md)
4. [Sécurité + Économie](04_security_economy.md)
5. [Méta-architecture + Quine](05_meta_quine.md)

## Diagramme des flux inter-strates

```
                    ┌─────────────────────────────────────┐
                    │   12 LOGOS — Langage, Raisonnement  │
                    │        (LLM + RAG + Reasoning)      │
                    └────────────┬────────────────────────┘
                                 │ ↑↓
                    ┌────────────┴────────────────────────┐
                    │   11 CHRONOS — Temps tri-directionnel│
                    │   (Scheduler + Sommeil + Prédiction) │
                    └────────────┬────────────────────────┘
                                 │ ↑↓
                    ┌────────────┴────────────────────────┐
                    │   10 CONSCIENCE — Global Workspace   │
                    │   (GWT + IIT + Free Energy)         │
                    └────────────┬────────────────────────┘
                                 │ ↑↓
        ┌────────────┬───────────┴──────────┬─────────────┐
        │            │                      │             │
┌───────┴────┐ ┌─────┴──────┐  ┌────────────┴──┐  ┌──────┴──────┐
│ 9 ANIMUS   │ │ 8 NOOSPHÈRE│  │ 7 FORGERON    │  │ 6 LABYRINTHE│
│ Émotions   │ │ Web + Sci. │  │ Skills + Ev.  │  │ Analyse     │
└─────┬──────┘ └─────┬──────┘  └───────┬───────┘  └──────┬──────┘
      │ ↑↓          │ ↑↓               │ ↑↓              │ ↑↓
      │     ┌───────┴──────────────────┴────────────────┘
      │     │
      │  ┌──┴─────────────────────────────────────────────┐
      │  │   5 ŒIL DU MONDE — Perception Universelle     │
      │  │   (12 sens : filesystem, API, channels...)    │
      │  └─────────────┬──────────────────────────────────┘
      │                │ ↑↓
      │  ┌─────────────┴──────────────────────────────────┐
      │  │   4 MÉMOIRE — Graphe Sémantique Vivant        │
      │  │   (8 types : episodic, semantic, procedural…) │
      │  └─────────────┬──────────────────────────────────┘
      │                │ ↑↓
      │  ┌─────────────┴──────────────────────────────────┐
      │  │   3 IMMUNE — Défense Totale                    │
      │  │   (12 catégories de menaces + FHE + ZKP)      │
      │  └─────────────┬──────────────────────────────────┘
      │                │ ↑↓
      │  ┌─────────────┴──────────────────────────────────┐
      │  │   2 ÉTHIQUE — Gardien des 4 Axiomes α,β,γ,δ    │
      │  │   (filter + transparency + reversibility)     │
      │  └─────────────┬──────────────────────────────────┘
      │                │
      │  ┌─────────────┴──────────────────────────────────┐
      │  │   1 NOYAU — Identité & Continuité Immuable     │
      │  │   (Ed25519 + UUID v7 + Axiomes signés)         │
      │  └────────────────────────────────────────────────┘
      │
      └──── ANIMUS ←── USAGER (interface)
```

## Transverses

| Transverse | Rôle | Phase cible |
|------------|------|-------------|
| **brain** | SNN, cartes corticales, Hopfield moderne | 2 (RAPHAËL) |
| **swarm** | CIEL-NET, Ruche, Raft, FedAvg | 4 (MANAS) |
| **security** | Post-quantique, FHE, ZKP, SMPC | 2 (RAPHAËL) |
| **economy** | Métabolisme, marché interne, Shapley | 4 (MANAS) |
| **quantum** | QAOA, VQE, superposition de croyances | 4 (MANAS) |
| **math** | Catégories, HoTT, géométrie informationnelle | 3 (CIEL) |
| **interfaces** | CLI, TUI, voice, canvas, API, ACP | 1-3 |
| **polyglot** | Bridge Rust/Go/C | 1+ |

## Communication inter-strates : Lingua Franca

Format 256 bits par message inter-strate :

```
[ORIGINE:Strate_N] [TYPE:signal_type] [GRAVITÉ:0.00-1.00]
[CONCEPT:concept_ID_array] [CAUSALITÉ:cause→effet]
[URGENCE:ÉCLAIR|PULSATION|...] [CONFIDENCE:0.00-1.00]
[TEMPORALITÉ:passé|présent|futur|méta]
[MÉTADONNÉES:JSON_compressé_LZ4]
[ACTION_PROPOSÉE:action_ID]
[SIGNATURE:HMAC-SHA256]
```

- Transmission inter-process en < 50ns (mémoire partagée cible)
- Chiffré en transit (ChaCha20-Poly1305)
- Vérification d'intégrité à chaque réception
