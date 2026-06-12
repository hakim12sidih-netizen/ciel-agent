"""Système adversarial socratique — 3 adversaires pour le combat de Phase 04."""
from __future__ import annotations

import random
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


ADVERSARY_PROFILES = {
    "domain_expert": {
        "name": "Expert du domaine",
        "tactics": ["precision", "counterexample", "citation", "formal_flaw"],
        "temperature": 0.3,
        "description": "Attaque technique précise — cherche les erreurs factuelles et logiques.",
    },
    "radical_skeptic": {
        "name": "Sceptique radical",
        "tactics": ["first_principles", "infinite_regress", "paradox", "presupposition"],
        "temperature": 0.9,
        "description": "Remet en cause les fondements mêmes de l'argumentation.",
    },
    "naive_challenger": {
        "name": "Challenger naïf",
        "tactics": ["simple_question", "analogy", "edge_case", "misunderstanding"],
        "temperature": 1.2,
        "description": "Questions simples qui révèlent des présupposés cachés.",
    },
}


class AdversarialAttack:
    """Une attaque unique générée par un profil adverse."""

    def __init__(self, profile: str, tactic: str, content: str):
        self.profile = profile
        self.tactic = tactic
        self.content = content

    def to_tensor(self, tokenizer) -> torch.Tensor:
        tokens = tokenizer.encode(self.content, add_special=True)
        return torch.tensor([tokens], dtype=torch.long)


class SocraticSystem:
    """Système de combat socratique à 3 adversaires.

    Chaque réponse du modèle est attaquée simultanément par 3 profils adverses.
    Le modèle doit défendre, réviser ou abandonner.
    """

    def __init__(self, model: nn.Module, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.attack_history: list[dict] = []

    def generate_attack(self, response_text: str, profile: str) -> AdversarialAttack:
        """Génère une attaque basée sur le profil adverse."""
        profile_info = ADVERSARY_PROFILES.get(profile, ADVERSARY_PROFILES["domain_expert"])
        tactic = random.choice(profile_info["tactics"])

        attack_templates = {
            "precision": f"Précise la base factuelle de : {response_text[:200]}",
            "counterexample": f"Contre-exemple possible à : {response_text[:200]}",
            "first_principles": f"Pourquoi ces prémisses plutôt que d'autres ? ({response_text[:100]})",
            "infinite_regress": f"Qu'est-ce qui justifie le justificateur ? ({response_text[:100]})",
            "simple_question": f"Explique comme si j'avais 5 ans : {response_text[:200]}",
            "paradox": f"Paradoxe dans l'argument : {response_text[:200]}",
            "edge_case": f"Cas limite : {response_text[:200]}",
            "analogy": f"Est-ce comparable à {random.choice(['une chaise', 'un rêve', 'un théorème', 'une recette de cuisine'])} ? ({response_text[:100]})",
        }

        content = attack_templates.get(tactic, f"Pourquoi ? ({response_text[:100]})")
        return AdversarialAttack(profile, tactic, content)

    def evaluate_defense(self, response_logits: torch.Tensor,
                         attack_logits: torch.Tensor) -> dict:
        """Évalue la qualité de la défense contre une attaque."""
        response_probs = F.softmax(response_logits, dim=-1)
        attack_probs = F.softmax(attack_logits, dim=-1)

        response_entropy = -(response_probs * torch.log(response_probs + 1e-8)).sum(dim=-1).mean()
        attack_entropy = -(attack_probs * torch.log(attack_probs + 1e-8)).sum(dim=-1).mean()

        confidence = response_probs.max(dim=-1).values.mean()
        uncertainty_gap = attack_entropy - response_entropy

        return {
            "confidence": confidence.item(),
            "response_entropy": response_entropy.item(),
            "attack_entropy": attack_entropy.item(),
            "uncertainty_gap": uncertainty_gap.item(),
            "defense_score": (confidence - uncertainty_gap * 0.1).item(),
        }

    def run_socratic_round(self, input_ids: torch.Tensor,
                           profiles: Optional[list[str]] = None) -> dict:
        """Un round complet de combat socratique."""
        if profiles is None:
            profiles = ["domain_expert", "radical_skeptic", "naive_challenger"]

        attacks = []
        defenses = []
        total_defense_score = 0.0

        for profile in profiles:
            attack_text = self.generate_attack("...response...", profile)
            attack_ids = attack_text.to_tensor(self.tokenizer)
            attacks.append(attack_text)

            with torch.no_grad():
                response = self.model(input_ids, return_logits=True)
                attack_response = self.model(
                    torch.cat([input_ids, attack_ids.to(input_ids.device)], dim=-1),
                    return_logits=True,
                )

            eval_result = self.evaluate_defense(
                response["logits"],
                attack_response["logits"],
            )
            defenses.append(eval_result)
            total_defense_score += eval_result["defense_score"]

        avg_score = total_defense_score / max(len(profiles), 1)
        is_defeated = avg_score < 0.3

        round_result = {
            "attacks": [{"profile": a.profile, "tactic": a.tactic, "content": a.content} for a in attacks],
            "defenses": defenses,
            "avg_defense_score": avg_score,
            "is_defeated": is_defeated,
        }
        self.attack_history.append(round_result)
        return round_result

    def socratic_loss(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Calcule la perte socratique à partir du round."""
        round_result = self.run_socratic_round(input_ids)
        if round_result["is_defeated"]:
            return torch.tensor(1.0, requires_grad=True) * 0.5
        return torch.tensor(1.0 - round_result["avg_defense_score"], requires_grad=True) * 0.1

    def get_statistics(self) -> dict:
        """Statistiques des rounds de combat."""
        if not self.attack_history:
            return {"rounds": 0, "avg_score": 0, "defeat_rate": 0}
        scores = [r["avg_defense_score"] for r in self.attack_history]
        defeats = sum(1 for r in self.attack_history if r["is_defeated"])
        return {
            "rounds": len(self.attack_history),
            "avg_score": sum(scores) / len(scores),
            "defeat_rate": defeats / len(self.attack_history),
            "total_attacks": sum(len(r["attacks"]) for r in self.attack_history),
        }
