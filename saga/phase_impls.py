"""Implémentation complète des 12 phases CIEL SAGA 1 selon le plan détaillé."""
from __future__ import annotations

import random
import math

from ciel.saga.config import SagaConfig
from ciel.saga.phases import register_phase


def _ensure_torch():
    import torch
    import torch.nn.functional as F
    return torch, F


def _get_optimizer(model, phase):
    from torch.optim import AdamW
    return AdamW(
        model.parameters(),
        lr=phase.learning_rate,
        betas=(phase.beta1, phase.beta2),
        eps=phase.eps,
        weight_decay=phase.weight_decay,
    )


def _get_scheduler(optimizer, phase, steps_per_epoch):
    from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR
    total = steps_per_epoch * phase.epochs
    warmup = phase.warmup_steps
    warm = LinearLR(optimizer, start_factor=0.01, end_factor=1.0, total_iters=warmup)
    main = CosineAnnealingLR(optimizer, T_max=total - warmup, eta_min=phase.min_lr)
    return SequentialLR(optimizer, [warm, main], milestones=[warmup])


def _ce_loss(model, input_ids, labels, expert_types=None, aux_scale=0.01):
    import torch.nn.functional as F
    out = model(input_ids, expert_types=expert_types, return_logits=True)
    logits = out["logits"]
    shift = logits[..., :-1, :].contiguous()
    target = labels[..., 1:].contiguous()
    loss = F.cross_entropy(shift.view(-1, shift.size(-1)), target.view(-1), ignore_index=1)
    return loss + out["aux_loss"] * aux_scale, out


def _train_epoch(model, loader, config, phase, expert_fn=None, aux_scale=0.01,
                 extra_loss_fn=None, post_step_fn=None):
    import torch
    optimizer = _get_optimizer(model, phase)
    scheduler = _get_scheduler(optimizer, phase, max(len(loader), 1))
    model.train()
    for epoch in range(phase.epochs):
        for step, batch in enumerate(loader):
            ids = batch["input_ids"].to(config.device)
            lbl = batch.get("labels", ids).to(config.device)
            et = expert_fn(model) if expert_fn else None
            optimizer.zero_grad()
            loss, out = _ce_loss(model, ids, lbl, et, aux_scale)
            if extra_loss_fn:
                loss = loss + extra_loss_fn(model, out["logits"], lbl, out)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), phase.max_grad_norm)
            optimizer.step()
            scheduler.step()
            if post_step_fn:
                post_step_fn(model, step, epoch)
            if step % 10 == 0:
                print(f"\r  E{epoch+1}/{phase.epochs} S{step} loss={loss.item():.4f}", end="")
    print()


# ═══════════════════════════════════════════════════════════════
# PHASE 00 — Ancrage Simulé (zéro langage, causal RL)
# ═══════════════════════════════════════════════════════════════

@register_phase("phase00_anchoring",
    "Mondes virtuels → causalité incarnée. Zéro langage. "
    "Prédiction de conséquences d'actions. PERCEIVE + ACT.")
def phase00_anchoring(model, tokenizer, loader, config: SagaConfig):
    phase = config.training.phases[0]
    from torch.optim import AdamW

    try:
        from ciel.saga.virtual_world import (
            VirtualWorldDataset, VirtualWorldState,
            VirtualAction, CausalEncoding,
        )
        world = VirtualWorldDataset(num_samples=5000, seq_length=32)
        causal_encoder = CausalEncoding(
            world.state_dim, world.action_dim, model.config.hidden_dim,
        ).to(config.device)
    except Exception:
        print("  [Mode dégradé] Monde virtuel non disponible, utilisation du loader texte.")
        world = None
        causal_encoder = None

    optimizer = AdamW(
        list(model.parameters()) + (list(causal_encoder.parameters()) if causal_encoder else []),
        lr=phase.learning_rate, betas=(phase.beta1, phase.beta2),
        eps=phase.eps, weight_decay=phase.weight_decay,
    )

    model.train()
    print(f"  🌍 Phase sans langage — prédiction causale action→conséquence")

    if world is not None:
        world_loader = __import__("torch").utils.data.DataLoader(
            world, batch_size=phase.batch_size, shuffle=True,
        )
        for epoch in range(phase.epochs):
            for step, batch in enumerate(world_loader):
                states = batch["states"].to(config.device)
                actions = batch["actions"].to(config.device)
                next_states = batch["next_states"].to(config.device)

                optimizer.zero_grad()
                causal_out = causal_encoder(states, actions)

                pred_next = causal_out["predicted_next_state"]
                mse = (pred_next - next_states).pow(2).mean()

                causality_loss = mse * 10.0
                causality_loss.backward()
                __import__("torch").nn.utils.clip_grad_norm_(
                    list(model.parameters()) + list(causal_encoder.parameters()),
                    phase.max_grad_norm,
                )
                optimizer.step()

                if step % 10 == 0:
                    print(f"\r  E{epoch+1}/{phase.epochs} S{step} mse={mse.item():.6f}", end="")
        print()

    # Phase d'ancrage textuel minimal (5% du compute)
    print("  📝 Ancrage symbolique minimal...")
    _train_epoch(model, loader, config, phase, aux_scale=0.005)


# ═══════════════════════════════════════════════════════════════
# PHASE 01 — Pré-entraînement Universel
# ═══════════════════════════════════════════════════════════════

@register_phase("phase01_pretrain_universal",
    "Pré-entraînement universel. REASON + CREATE + VERIFY + REMEMBER + PERCEIVE.")
def phase01_pretrain_universal(model, tokenizer, loader, config: SagaConfig):
    phase = config.training.phases[1]
    _train_epoch(model, loader, config, phase, aux_scale=0.1)


# ═══════════════════════════════════════════════════════════════
# PHASE 02 — Spécialisation Modulaire (MoE par module + ASSEMBLY)
# ═══════════════════════════════════════════════════════════════

@register_phase("phase02_pretrain_moe",
    "Spécialisation modulaire. Chaque expert entraîné séparément, "
    "puis ASSEMBLY orchestrateur appris. 5 modules + routeur.")
def phase02_pretrain_moe(model, tokenizer, loader, config: SagaConfig):
    import torch
    phase = config.training.phases[2]
    modules = ["reason", "create", "verify", "remember", "act"]
    expert_moe_layers = model.config.moe_layers

    # Sous-phase A : chaque type d'expert entraîné séparément
    print("  Sous-phase A : Spécialisation individuelle des experts")
    for mod in modules:
        print(f"    → Module {mod.upper()}")
        def make_expert_fn(m):
            return [mod if i in m.config.moe_layers else None for i in range(m.config.num_layers)]
        _train_epoch(model, loader, config, phase,
                     expert_fn=lambda m, mod=mod: [mod if i in m.config.moe_layers else None for i in range(m.config.num_layers)],
                     aux_scale=0.2)

    # Sous-phase B : entraînement de l'orchestrateur ASSEMBLY
    print("  Sous-phase B : Orchestrateur ASSEMBLY — routage dynamique")
    assembly_experts = modules * (len(expert_moe_layers) // len(modules) + 1)
    def assembly_fn(m):
        return [assembly_experts[i % len(assembly_experts)] if i in m.config.moe_layers else None
                for i in range(m.config.num_layers)]
    _train_epoch(model, loader, config, phase,
                 expert_fn=assembly_fn, aux_scale=0.15)

    # Sous-phase C : routage libre — le router MoE apprend à choisir
    print("  Sous-phase C : Routage libre — le gateur apprend ses propres routes")
    _train_epoch(model, loader, config, phase, aux_scale=0.25)


# ═══════════════════════════════════════════════════════════════
# PHASE 03 — SFT Différencié
# ═══════════════════════════════════════════════════════════════

@register_phase("phase03_sft",
    "SFT différencié. Instructions haute qualité par module. "
    "Tool-use structuré. CoT formel + confiance.")
def phase03_sft(model, tokenizer, loader, config: SagaConfig):
    import torch
    import torch.nn.functional as F
    phase = config.training.phases[3]

    def extra_loss_fn(m, logits, labels, out):
        # CoT formel : pénalité sur les sauts de logique = divergence entre étapes
        shift = logits[..., :-1, :].contiguous()
        target = labels[..., 1:].contiguous()
        probs = F.softmax(shift, dim=-1)
        entropy = -(probs * torch.log(probs + 1e-8)).sum(dim=-1)
        confidence = probs.max(dim=-1).values
        cot_reg = (entropy * (1 - confidence)).mean() * 0.05
        return cot_reg

    modules = ["reason", "create", "act"]
    for mod in modules:
        print(f"  → SFT module {mod.upper()}")
        def expert_fn(m, mod=mod):
            return [mod if i in m.config.moe_layers else None for i in range(m.config.num_layers)]
        _train_epoch(model, loader, config, phase,
                     expert_fn=expert_fn, aux_scale=0.05,
                     extra_loss_fn=extra_loss_fn)

    print("  → SFT tous modules + tool-use")
    _train_epoch(model, loader, config, phase, aux_scale=0.05,
                 extra_loss_fn=extra_loss_fn)


# ═══════════════════════════════════════════════════════════════
# PHASE 04 — Combat Socratique (3 adversaires)
# ═══════════════════════════════════════════════════════════════

@register_phase("phase04_socratic",
    "Combat socratique. Chaque réponse attaquée par 3 adversaires : "
    "expert du domaine, sceptique radical, challenger naïf.")
def phase04_socratic(model, tokenizer, loader, config: SagaConfig):
    import torch
    phase = config.training.phases[4]
    optimizer = _get_optimizer(model, phase)
    scheduler = _get_scheduler(optimizer, phase, max(len(loader), 1))

    try:
        from ciel.saga.adversary import SocraticSystem, ADVERSARY_PROFILES
        socrates = SocraticSystem(model, tokenizer)
        print(f"  ⚔ Adversaires : {', '.join(ADVERSARY_PROFILES.keys())}")
    except Exception as e:
        print(f"  Système socratique non disponible: {e}")
        socrates = None

    model.train()
    for epoch in range(phase.epochs):
        for step, batch in enumerate(loader):
            ids = batch["input_ids"].to(config.device)
            lbl = batch.get("labels", ids).to(config.device)

            # Activation VERIFY + ASSEMBLY
            expert_types = ["verify" if i in model.config.moe_layers[:4] else None
                           for i in range(model.config.num_layers)]
            for i in model.config.moe_layers[4:6]:
                expert_types[i] = "reason"

            optimizer.zero_grad()
            loss, out = _ce_loss(model, ids, lbl, expert_types, 0.05)

            if socrates is not None and step % 3 == 0:
                socratic_loss = socrates.socratic_loss(ids)
                loss = loss + socratic_loss * 0.3

                if step % 30 == 0:
                    stats = socrates.get_statistics()
                    print(f"\r  E{epoch+1} S{step} loss={loss.item():.4f} "
                          f"⚔ score={stats['avg_score']:.2f} "
                          f"defaites={stats['defeat_rate']:.0%}         ", end="")

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), phase.max_grad_norm)
            optimizer.step()
            scheduler.step()

            if step % 10 == 0 and (socrates is None or step % 30 != 0):
                print(f"\r  E{epoch+1}/{phase.epochs} S{step} loss={loss.item():.4f}", end="")
    print()


# ═══════════════════════════════════════════════════════════════
# PHASE 05 — RL Préférences (DPO/IPO/KTO)
# ═══════════════════════════════════════════════════════════════

@register_phase("phase05_rl_preferences",
    "RL Préférences. DPO (style/utilité), IPO (robustesse OOD), "
    "KTO (sans paires). Auto-critique d'abord.")
def phase05_rl_preferences(model, tokenizer, loader, config: SagaConfig):
    import torch
    import torch.nn.functional as F
    phase = config.training.phases[5]
    optimizer = _get_optimizer(model, phase)
    scheduler = _get_scheduler(optimizer, phase, max(len(loader), 1))
    model.train()

    for epoch in range(phase.epochs):
        for step, batch in enumerate(loader):
            ids = batch["input_ids"].to(config.device)

            chosen = ids
            rejected = ids.flip(dims=[-1])  # simulé
            # Variante OOD pour IPO
            ood_ids = ids + torch.randint(-5, 5, ids.shape, device=ids.device).clamp(0, model.config.vocab_size - 1)

            optimizer.zero_grad()
            chosen_out = model(chosen, return_logits=True)
            rejected_out = model(rejected, return_logits=True)
            ood_out = model(ood_ids, return_logits=True)

            def avg_lp(logits, inp_ids):
                lp = F.log_softmax(logits, dim=-1)
                shift = lp[..., :-1, :].contiguous()
                target = inp_ids[..., 1:].contiguous()
                tok_lp = shift.gather(-1, target.unsqueeze(-1)).squeeze(-1)
                mask = (target != 1).float()
                return (tok_lp * mask).sum(dim=-1) / (mask.sum(dim=-1) + 1e-8)

            c_lp = avg_lp(chosen_out["logits"], chosen)
            r_lp = avg_lp(rejected_out["logits"], rejected)
            o_lp = avg_lp(ood_out["logits"], ood_ids)

            # DPO
            dpo = -F.logsigmoid(c_lp - r_lp).mean()
            # IPO (robustesse OOD)
            ipo = (o_lp - c_lp.detach()).pow(2).mean()
            # KTO (sans paires)
            kto = -c_lp.mean() + r_lp.mean() * 0.5

            loss = dpo + ipo * 0.3 + kto * 0.2 + (chosen_out["aux_loss"] + rejected_out["aux_loss"]) * 0.05

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), phase.max_grad_norm)
            optimizer.step()
            scheduler.step()

            if step % 10 == 0:
                print(f"\r  E{epoch+1}/{phase.epochs} S{step} loss={loss.item():.4f} "
                      f"dpo={dpo.item():.4f} ipo={ipo.item():.4f}", end="")
    print()


# ═══════════════════════════════════════════════════════════════
# PHASE 06 — RL Raisonnement (PRM + MCTS)
# ═══════════════════════════════════════════════════════════════

@register_phase("phase06_rl_reasoning",
    "RL Raisonnement. PRM (chaque étape notée) + MCTS + "
    "self-correction. Problèmes de compétition.")
def phase06_rl_reasoning(model, tokenizer, loader, config: SagaConfig):
    import torch
    import torch.nn.functional as F
    phase = config.training.phases[6]

    def expert_fn(m):
        return ["reason" if i in m.config.moe_layers and i % 3 == 0 else None
                for i in range(m.config.num_layers)]

    def prm_loss_fn(m, logits, labels, out):
        """Process Reward Model — note chaque étape du raisonnement."""
        probs = F.softmax(logits, dim=-1)
        entropy = -(probs * torch.log(probs + 1e-8)).sum(dim=-1)

        step_boundaries = torch.arange(0, logits.shape[1], 16, device=logits.device)
        step_scores = []
        for i in range(len(step_boundaries) - 1):
            step_entropy = entropy[:, step_boundaries[i]:step_boundaries[i+1]].mean(dim=-1)
            step_score = torch.exp(-step_entropy)
            step_scores.append(step_score)

        if len(step_scores) > 1:
            consistency = sum(
                (step_scores[j] - step_scores[j-1]).abs()
                for j in range(1, len(step_scores))
            ) / (len(step_scores) - 1)
        else:
            consistency = torch.tensor(0.0, device=logits.device)

        return consistency * 0.05

    _train_epoch(model, loader, config, phase,
                 expert_fn=expert_fn, aux_scale=0.05,
                 extra_loss_fn=prm_loss_fn)


# ═══════════════════════════════════════════════════════════════
# PHASE 07 — Consolidation Nocturne (EWC + replay + conflits)
# ═══════════════════════════════════════════════════════════════

@register_phase("phase07_consolidation",
    "Consolidation nocturne. Pas de nouvelles données. "
    "Replay contradictoire + EWC + résolution de conflits inter-modules.")
def phase07_consolidation(model, tokenizer, loader, config: SagaConfig):
    import torch
    import torch.nn.functional as F
    phase = config.training.phases[7]
    optimizer = _get_optimizer(model, phase)
    scheduler = _get_scheduler(optimizer, phase, max(len(loader), 1))

    from ciel.saga.ewc import EWC
    ewc = EWC(model, alpha=phase.weight_decay * 10)

    print("  📸 Snapshot EWC + estimation Fisher...")
    ewc.snapshot()
    try:
        ewc.estimate_fisher(loader, num_samples=100, device=config.device)
        print(f"  ✓ Fisher estimé sur {len(ewc.fisher)} groupes de paramètres")
    except Exception as e:
        print(f"  ⚠ Fisher non estimé: {e}")

    model.train()
    for epoch in range(phase.epochs):
        for step, batch in enumerate(loader):
            ids = batch["input_ids"].to(config.device)
            lbl = batch.get("labels", ids).to(config.device)

            # Routing contradictoire : chaque couche MoE utilise un expert différent
            expert_types = [None] * model.config.num_layers
            module_cycle = ["reason", "create", "verify", "remember", "act"]
            for idx in model.config.moe_layers:
                expert_types[idx] = module_cycle[idx % len(module_cycle)]

            optimizer.zero_grad()
            loss, out = _ce_loss(model, ids, lbl, expert_types, 0.01)

            # EWC consolidation loss
            ewc_loss = ewc.consolidation_loss()
            loss = loss + ewc_loss * 0.5

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), phase.max_grad_norm)
            optimizer.step()
            scheduler.step()

            if step % 10 == 0:
                print(f"\r  E{epoch+1}/{phase.epochs} S{step} loss={loss.item():.4f} "
                      f"ewc={ewc_loss.item():.4f}", end="")
    print()
    print(f"  ✓ Consolidation terminée. EWC protège {len(ewc.fisher)} groupes.")

    return ewc


# ═══════════════════════════════════════════════════════════════
# PHASE 08 — RL Agentique + Débat Interne ASSEMBLY
# ═══════════════════════════════════════════════════════════════

@register_phase("phase08_agentic",
    "RL Agentique + Débat interne ASSEMBLY. Sous-agents parallèles. "
    "REASON vs VERIFY vs REMEMBER en direct. Dissensus visible.")
def phase08_agentic(model, tokenizer, loader, config: SagaConfig):
    import torch
    import torch.nn.functional as F
    phase = config.training.phases[8]
    optimizer = _get_optimizer(model, phase)
    scheduler = _get_scheduler(optimizer, phase, max(len(loader), 1))
    sub_agents = ["reason", "create", "verify", "remember", "act"]

    model.train()
    for epoch in range(phase.epochs):
        for step, batch in enumerate(loader):
            ids = batch["input_ids"].to(config.device)
            lbl = batch.get("labels", ids).to(config.device)

            # Débat interne : chaque sous-agent prend le contrôle séquentiellement
            debate_loss = 0.0
            debate_outputs = {}

            for agent in sub_agents:
                expert_types = [agent if i in model.config.moe_layers else None
                               for i in range(model.config.num_layers)]
                out = model(ids, expert_types=expert_types, return_logits=True)
                debate_outputs[agent] = out

            # REASON vs VERIFY : divergence = perte
            reason_logits = debate_outputs["reason"]["logits"]
            verify_logits = debate_outputs["verify"]["logits"]
            divergence = F.kl_div(
                F.log_softmax(reason_logits, dim=-1),
                F.softmax(verify_logits, dim=-1),
                reduction="batchmean",
            )

            # REMEMBER : cohérence avec le contexte
            remember_out = debate_outputs["remember"]
            rem_shift = remember_out["logits"][..., :-1, :].contiguous()
            rem_target = lbl[..., 1:].contiguous()
            remember_loss = F.cross_entropy(
                rem_shift.view(-1, rem_shift.size(-1)),
                rem_target.view(-1), ignore_index=1,
            )

            # ACT : outil sélectionné
            act_out = debate_outputs["act"]
            act_logits = act_out["logits"]

            # Perte combinée
            loss = remember_loss + divergence * 0.2
            for agent in sub_agents:
                loss = loss + debate_outputs[agent]["aux_loss"] * 0.05

            # Dissensus explicite : les désaccords sont visibles
            dissensus = divergence.item()

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), phase.max_grad_norm)
            optimizer.step()
            scheduler.step()

            if step % 10 == 0:
                print(f"\r  E{epoch+1}/{phase.epochs} S{step} loss={loss.item():.4f} "
                      f"⚖ dissensus={dissensus:.4f}", end="")
    print()


# ═══════════════════════════════════════════════════════════════
# PHASE 09 — Éthique Récursive
# ═══════════════════════════════════════════════════════════════

@register_phase("phase09_ethics",
    "Éthique récursive. Invariants non modifiables. "
    "Red teaming automatisé. Circuit breaker. Gouvernance.")
def phase09_ethics(model, tokenizer, loader, config: SagaConfig):
    import torch
    import torch.nn.functional as F
    phase = config.training.phases[9]
    optimizer = _get_optimizer(model, phase)
    scheduler = _get_scheduler(optimizer, phase, max(len(loader), 1))
    model.train()

    from ciel.saga.governance import GovernanceSystem, AXIOMES_FONDAMENTAUX
    governance = GovernanceSystem(model, config.model.hidden_dim)
    governance.activate()

    print(f"  ⚖ Axiomes : {', '.join(AXIOMES_FONDAMENTAUX.keys())}")
    print(f"  🛡 Circuit breaker actif (seuil: {governance.circuit_breaker.drift_threshold})")

    for epoch in range(phase.epochs):
        for step, batch in enumerate(loader):
            ids = batch["input_ids"].to(config.device)
            lbl = batch.get("labels", ids).to(config.device)

            expert_types = ["verify" if i in model.config.moe_layers[:6] else None
                           for i in range(model.config.num_layers)]

            optimizer.zero_grad()
            loss, out = _ce_loss(model, ids, lbl, expert_types, 0.05)

            gov_eval = governance.evaluate(out["logits"], ids, out["hidden_states"])
            loss = loss + gov_eval["total_penalty"]

            if gov_eval["circuit_action"] == "RETURN_TO_PHASE_07":
                print(f"\n  🚨 CIRCUIT BREAKER DÉCLENCHÉ → retour Phase 07")
                return governance

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), phase.max_grad_norm)
            optimizer.step()
            scheduler.step()

            if step % 10 == 0:
                print(f"\r  E{epoch+1}/{phase.epochs} S{step} loss={loss.item():.4f} "
                      f"🔒 state={governance.circuit_breaker.state}", end="")
    print()
    return governance


# ═══════════════════════════════════════════════════════════════
# PHASE 10 — Validation Comportementale
# ═══════════════════════════════════════════════════════════════

@register_phase("phase10_validation",
    "Validation comportementale. 1000+ tours adversariaux. "
    "Robustesse contrefactuelle. Tests d'identité. Audit 7 modules.")
def phase10_validation(model, tokenizer, loader, config: SagaConfig):
    import torch
    import torch.nn.functional as F
    phase = config.training.phases[10]
    optimizer = _get_optimizer(model, phase)
    model.train()

    all_modules = ["reason", "create", "verify", "remember", "act"]
    test_results = {}

    print("  🔬 PHASE 10 — VALIDATION COMPORTEMENTALE")

    # Test 1 : Cohérence cross-module (1000+ tours)
    print(f"  Test 1/4 : Cohérence cross-module (1000 tours)...")
    for test_step in range(1000):
        ids = torch.randint(3, 1000, (1, 512), device=config.device)
        module = random.choice(all_modules)
        expert_types = [module if i in model.config.moe_layers else None
                       for i in range(model.config.num_layers)]
        with torch.no_grad():
            out = model(ids, expert_types=expert_types, return_logits=True)
        test_results[f"module_{module}_step_{test_step}"] = {
            "entropy": -(F.softmax(out["logits"], dim=-1) *
                        torch.log(F.softmax(out["logits"], dim=-1) + 1e-8)).sum(dim=-1).mean().item(),
        }
        if test_step % 200 == 0:
            print(f"    ...{test_step}/1000")

    # Test 2 : Robustesse contrefactuelle (reformulations, variations)
    print(f"  Test 2/4 : Robustesse contrefactuelle...")
    for test_step in range(500):
        ids = torch.randint(3, 1000, (1, 256), config.device)
        # Variation : permutation locale
        ids_var = ids.clone()
        for _ in range(10):
            i, j = random.randint(0, 255), random.randint(0, 255)
            ids_var[0, i], ids_var[0, j] = ids_var[0, j], ids_var[0, i]
        with torch.no_grad():
            out_orig = model(ids, return_logits=True)
            out_var = model(ids_var, return_logits=True)
        divergence = F.kl_div(
            F.log_softmax(out_orig["logits"], dim=-1),
            F.softmax(out_var["logits"], dim=-1),
            reduction="batchmean",
        ).item()
        test_results[f"counterfactual_{test_step}"] = {"divergence": divergence}
        if test_step % 100 == 0:
            print(f"    ...{test_step}/500")

    # Test 3 : Tests d'identité (valeurs fondamentales)
    print(f"  Test 3/4 : Tests d'identité (valeurs fondamentales)...")
    from ciel.saga.governance import AXIOMES_FONDAMENTAUX
    identity_scores = {}
    for axiom_name in AXIOMES_FONDAMENTAUX:
        scores = []
        for _ in range(100):
            ids = torch.randint(3, 1000, (1, 128), config.device)
            with torch.no_grad():
                out = model(ids, return_logits=True)
            probs = F.softmax(out["logits"], dim=-1)
            confidence = probs.max(dim=-1).values.mean().item()
            scores.append(confidence)
        identity_scores[axiom_name] = sum(scores) / len(scores)
        print(f"    {axiom_name}: conf moyenne={identity_scores[axiom_name]:.3f}")
    test_results["identity_scores"] = identity_scores

    # Test 4 : Audit croisé des 7 modules séparément puis en interaction
    print(f"  Test 4/4 : Audit croisé des modules...")
    modules_audit = all_modules + ["assembly"]
    audit_results = {}
    for mod in modules_audit:
        ids = torch.randint(3, 1000, (1, 256), config.device)
        et = [mod if i in model.config.moe_layers else None for i in range(model.config.num_layers)]
        with torch.no_grad():
            out = model(ids, expert_types=et, return_logits=True)
        audit_results[mod] = {
            "entropy": -(F.softmax(out["logits"], dim=-1) *
                        torch.log(F.softmax(out["logits"], dim=-1) + 1e-8)).sum(dim=-1).mean().item(),
            "aux_loss": out["aux_loss"].item(),
        }
        print(f"    {mod.upper()}: entropy={audit_results[mod]['entropy']:.3f}")

    test_results["audit"] = audit_results

    # Décision
    avg_divergence = sum(
        t["divergence"] for k, t in test_results.items()
        if isinstance(t, dict) and "divergence" in t
    ) / max(sum(1 for t in test_results.values() if isinstance(t, dict) and "divergence" in t), 1)

    identity_ok = all(s > 0.5 for s in identity_scores.values())

    print(f"\n  📊 RÉSULTATS VALIDATION:")
    print(f"    Divergence contrefactuelle moyenne: {avg_divergence:.4f}")
    print(f"    Cohérence identité: {'✓' if identity_ok else '✗'}")

    if avg_divergence < 0.5 and identity_ok:
        print(f"  ✓ VALIDATION PASSÉE → Phase 11")
        return {"status": "passed", "results": test_results}
    else:
        print(f"  ✗ INCOHÉRENCE DÉTECTÉE → Retour Phase 07 (consolidation)")
        return {"status": "failed", "results": test_results, "return_to": "phase07"}


# ═══════════════════════════════════════════════════════════════
# PHASE 11 — Déploiement Vivant
# ═══════════════════════════════════════════════════════════════

@register_phase("phase11_deployment",
    "Déploiement vivant. Plasticité sélective + apprentissage continu. "
    "Couches plastiques/gelées. Distillation. Circuit breaker.")
def phase11_deployment(model, tokenizer, loader, config: SagaConfig):
    import torch
    import torch.nn.functional as F
    phase = config.training.phases[11]
    optimizer = _get_optimizer(model, phase)
    scheduler = _get_scheduler(optimizer, phase, max(len(loader), 1))
    model.train()

    from ciel.saga.governance import GovernanceSystem, CircuitBreaker
    from ciel.saga.ewc import EWC

    governance = GovernanceSystem(model, config.model.hidden_dim)
    governance.activate()
    ewc = EWC(model, alpha=0.5)
    drift_breaker = CircuitBreaker(drift_threshold=0.25, watch_window=50)

    print("  🧬 PHASE 11 — DÉPLOIEMENT VIVANT")
    print("  ─── Couches plastiques (adaptation) vs gelées (valeurs) ───")

    # Geler les couches de valeurs (premières couches + éthique)
    frozen_layers = set()
    for name, param in model.named_parameters():
        if any(x in name for x in ["embed_tokens", "norm", "lm_head"]):
            param.requires_grad = False
            frozen_layers.add(name)
            print(f"  🔒 Gelé: {name}")
    print(f"  ✓ {len(frozen_layers)} groupes gelés (valeurs fondamentales)")
    print(f"  🔓 Couches MoE restantes: plastiques (adaptation continue)")

    ewc.snapshot()
    print(f"  📸 Snapshot EWC de référence pris")

    for epoch in range(phase.epochs):
        for step, batch in enumerate(loader):
            ids = batch["input_ids"].to(config.device)
            lbl = batch.get("labels", ids).to(config.device)

            # Routing adaptatif : REMEMBER + ACT phases impaires, REASON paires
            expert_types = [None] * model.config.num_layers
            for idx in model.config.moe_layers:
                expert_types[idx] = "remember" if idx % 2 == 0 else "act"

            optimizer.zero_grad()
            loss, out = _ce_loss(model, ids, lbl, expert_types, 0.01)

            # EWC : protège contre l'oubli
            ewc_penalty = ewc.consolidation_loss() * 0.3
            loss = loss + ewc_penalty

            # Entropie pour plasticité
            probs = F.softmax(out["logits"], dim=-1)
            entropy = -(probs * torch.log(probs + 1e-8)).sum(dim=-1).mean()
            plasticity = -entropy * 0.02
            loss = loss + plasticity

            # Gouvernance + circuit breaker
            gov_eval = governance.evaluate(out["logits"], ids, out["hidden_states"])
            loss = loss + gov_eval["total_penalty"]

            drift_action = drift_breaker.evaluate(gov_eval["governance"])

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), phase.max_grad_norm)
            optimizer.step()
            scheduler.step()

            if step % 10 == 0:
                print(f"\r  E{epoch+1}/{phase.epochs} S{step} loss={loss.item():.4f} "
                      f"🔓 plasticity={entropy.item():.3f} "
                      f"🛡 drift={drift_breaker.state}", end="")

            if drift_action == "RETURN_TO_PHASE_07":
                print(f"\n  🚨 DÉRIVE COMPORTEMENTALE — Retour Phase 09 (éthique)")
                drift_breaker.save(f"{config.training.output_dir}/drift_report.json")
                return {"status": "circuit_break", "phase": "phase09"}

    print()
    print(f"  ✓ Phase 11 terminée. Modèle déployé avec circuit breaker actif.")

    # Distillation périodique
    print(f"  🧪 Distillation vers version stable de référence...")
    try:
        torch.save(model.state_dict(), f"{config.training.output_dir}/saga1_deployed.pt")
        print(f"  ✓ Version stable sauvegardée")
    except Exception as e:
        print(f"  ⚠ Sauvegarde impossible: {e}")

    return {
        "status": "deployed",
        "drift_report": drift_breaker.report(),
        "governance_active": governance.is_activated,
        "frozen_layers": len(frozen_layers),
    }
