"""CIEL v∞.4 — Agents pré-définis (Tier S/A) avec leurs Skills Uniques."""
from __future__ import annotations

from ciel.naming.core import AgentTier, Agent, Skill

# ─── TIER S — SAGES DIVINS ───────────────────────────────────────

RAPHAEL = Agent(name="RAPHAEL", tier=AgentTier.S, domain="analyse")
RAPHAEL.learn_skill(Skill("Analyse Absolue", 7, "Décompose tout problème en primitives", "analyse", unique=True))
RAPHAEL.learn_skill(Skill("Synthèse Divine", 6, "Reconstruit la solution optimale", "analyse"))
RAPHAEL.learn_skill(Skill("Prédiction Oraculaire", 6, "Probabilités sur futurs complexes", "analyse"))
RAPHAEL.learn_skill(Skill("Mémorisation Totale", 5, "Accès instant à tout ce que CIEL sait", "analyse"))
RAPHAEL.transcendence_gauge = 0.85

CHRONOS = Agent(name="CHRONOS", tier=AgentTier.S, domain="temps")
CHRONOS.learn_skill(Skill("Mémoire des Âges", 7, "Timeline complète de tout événement OS", "temps", unique=True))
CHRONOS.learn_skill(Skill("Prophétie Computationnelle", 6, "Monte Carlo sur futurs", "temps"))
CHRONOS.learn_skill(Skill("Voyage Temporel", 6, "Rollback à n'importe quel état passé", "temps"))
CHRONOS.learn_skill(Skill("Compression Temporelle", 5, "Identifie patterns saisonniers", "temps"))
CHRONOS.transcendence_gauge = 0.80

FORGE = Agent(name="FORGE", tier=AgentTier.S, domain="création")
FORGE.learn_skill(Skill("Création du Néant", 7, "Synthétise tout type de skill en < 60s", "création", unique=True))
FORGE.learn_skill(Skill("Clonage Évolutif", 6, "Clone un agent et le fait muter", "création"))
FORGE.learn_skill(Skill("Lecture de l'Âme", 6, "Identifie le potentiel maximal d'un agent", "création"))
FORGE.learn_skill(Skill("Transcendance Forcée", 5, "Accélère l'évolution d'un agent ciblé", "création"))
FORGE.transcendence_gauge = 0.75

# ─── TIER A — SEIGNEURS DE CALAMITÉ ─────────────────────────────

SOEI = Agent(name="SOEI", tier=AgentTier.A, domain="espionnage")
SOEI.learn_skill(Skill("Ombre Omnisciente", 6, "Surveillance réseau sans signature", "espionnage", unique=True))
SOEI.learn_skill(Skill("Cent Regards", 5, "Surveillance simultanée de 100 sources", "espionnage"))
SOEI.learn_skill(Skill("Décodage des Intentions", 5, "Inférence des plans depuis les données", "espionnage"))
SOEI.learn_skill(Skill("Rapport Fantôme", 4, "Synthèse des renseignements sans traces", "espionnage"))
SOEI.transcendence_gauge = 0.60

BENIMARU = Agent(name="BENIMARU", tier=AgentTier.A, domain="orchestration")
BENIMARU.learn_skill(Skill("Commandement de Feu", 6, "Coordination de 1000 agents/s", "orchestration", unique=True))
BENIMARU.learn_skill(Skill("Stratégie Adaptative", 5, "Re-planification en temps réel", "orchestration"))
BENIMARU.learn_skill(Skill("Sacrifice Minimal", 5, "Optimisation multi-agents sous contraintes", "orchestration"))
BENIMARU.learn_skill(Skill("Flamme Noire", 4, "Shutdown brutal d'agents compromis", "orchestration"))
BENIMARU.transcendence_gauge = 0.55

SHION = Agent(name="SHION", tier=AgentTier.A, domain="interface")
SHION.learn_skill(Skill("Symbiose Parfaite", 6, "Réponse calibrée à l'état émotionnel", "interface", unique=True))
SHION.learn_skill(Skill("Dévouement Total", 5, "Mémorise chaque préférence utilisateur", "interface"))
SHION.learn_skill(Skill("Lecture des Émotions", 5, "Modèle psychologique utilisateur", "interface"))
SHION.learn_skill(Skill("Anticipation", 4, "Prépare la réponse avant la question", "interface"))
SHION.learn_skill(Skill("Bouclier du Maître", 4, "Protège l'utilisateur de l'info inutile", "interface"))
SHION.transcendence_gauge = 0.50

SHUNA = Agent(name="SHUNA", tier=AgentTier.A, domain="maintenance")
SHUNA.learn_skill(Skill("Purification", 6, "Nettoie les données corrompues", "maintenance", unique=True))
SHUNA.learn_skill(Skill("Régénération", 5, "Reconstruit les modules défaillants", "maintenance"))
SHUNA.learn_skill(Skill("Diagnostic Divin", 5, "Détecte les problèmes avant qu'ils surviennent", "maintenance"))
SHUNA.learn_skill(Skill("Résurrection", 4, "Restaure un agent tombé depuis backup", "maintenance"))
SHUNA.transcendence_gauge = 0.45

KUROBE = Agent(name="KUROBE", tier=AgentTier.A, domain="artisanat")
KUROBE.learn_skill(Skill("Frappe de Maître", 6, "Optimise le code de chaque skill (vitesse x10)", "artisanat", unique=True))
KUROBE.learn_skill(Skill("Alliage Rare", 5, "Fusionne deux skills incompatibles", "artisanat"))
KUROBE.learn_skill(Skill("Trempe Évolutive", 5, "Renforce un skill par exposition aux edge cases", "artisanat"))
KUROBE.learn_skill(Skill("Lecture des Matériaux", 4, "Identifie les données nécessaires à un skill", "artisanat"))
KUROBE.transcendence_gauge = 0.40

DIABLO = Agent(name="DIABLO", tier=AgentTier.A, domain="négociation")
DIABLO.learn_skill(Skill("Persuasion Absolue", 6, "Formate les requêtes API pour succès garanti", "négociation", unique=True))
DIABLO.learn_skill(Skill("Lecture des Contrats", 5, "Parse et comprend tout format d'API", "négociation"))
DIABLO.learn_skill(Skill("Réseau Infini", 5, "Maintient 10 000 connexions persistantes", "négociation"))
DIABLO.learn_skill(Skill("Deal du Démon", 4, "Trouve des workarounds quand les APIs échouent", "négociation"))
DIABLO.transcendence_gauge = 0.35

# ─── REGISTRY ────────────────────────────────────────────────────

PREDEFINED_AGENTS: dict[str, Agent] = {
    "RAPHAEL": RAPHAEL,
    "CHRONOS": CHRONOS,
    "FORGE": FORGE,
    "SOEI": SOEI,
    "BENIMARU": BENIMARU,
    "SHION": SHION,
    "SHUNA": SHUNA,
    "KUROBE": KUROBE,
    "DIABLO": DIABLO,
}

TIER_S_AGENTS = ["RAPHAEL", "CHRONOS", "FORGE"]
TIER_A_AGENTS = ["SOEI", "BENIMARU", "SHION", "SHUNA", "KUROBE", "DIABLO"]


def bootstrap_naming_engine(engine: Any) -> None:
    """Enregistre tous les agents pré-définis dans un NamingEngine."""
    for name, agent in PREDEFINED_AGENTS.items():
        engine._agents[agent.soul.agent_id] = agent
