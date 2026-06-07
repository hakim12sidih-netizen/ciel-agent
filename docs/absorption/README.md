# Absorption Strategy — ADR (Architecture Decision Records)

Ce dossier documente les décisions d'absorption de projets existants
dans CIEL. Chaque ADR suit le format :

- **Statut** : proposé / accepté / rejeté / remplacé
- **Date** : YYYY-MM-DD
- **Contexte** : projet source + raison d'absorption
- **Décision** : ce qui est absorbé, ce qui est jeté, comment
- **Conséquences** : positives, négatives, risques

## ADR Index

| ID | Titre | Statut |
|----|-------|--------|
| (à venir) | Absorption HYDRA | Proposé |
| (à venir) | Absorption Hermes Agent | Proposé |
| (à venir) | Absorption OpenClaw | Proposé |
| (à venir) | Stratégie polyglot Rust/Go | Proposé |

## Principes d'absorption

1. **On absorbe l'architecture, on ré-implémente le code** (jamais de copie 1:1)
2. **Tests obligatoires** : chaque absorption doit avoir 100% des tests
   originaux qui passent dans CIEL
3. **Pas de dette technique** : aucune ligne legacy ne doit entrer
   sans avoir été ré-écrite selon nos standards (types stricts,
   async, pydantic, etc.)
4. **Documente les rejets** : expliquer ce qu'on jette et pourquoi
5. **Compatibilité ascendante** : un user de HYDRA peut migrer
   sans douleur (mêmes APIs, mêmes CLI args)
