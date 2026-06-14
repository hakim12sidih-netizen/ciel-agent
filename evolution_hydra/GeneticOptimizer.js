/**
 * ═══════════════════════════════════════════════════════════════
 * GENETIC-OPTIMIZER v2 — Pilote l'évolution génétique
 * ═══════════════════════════════════════════════════════════════
 *
 * PHASE 2 : Refactorisé pour :
 * 1. Ajouter `absorbInto(survivor, victim)` : vraie fusion génomique
 * 2. Ajouter `generateHeirsFrom(chief, partner)` : vrais héritiers UnifiedGenome
 * 3. Conserver `mutateFaction` (signature legacy) mais l'implémenter
 *    avec de vrais mutations (au lieu du stub HydraNerveSystem)
 *
 * Le `Genome` interface local (velocity/precision/...) est conservé
 * pour rétro-compatibilité — c'est un "profil de personnalité"
 * dérivé, pas un génome complet.
 */
import logger from '../utils/logger.js';
import { ChromosomeType } from './UnifiedGenome.js';
export var Faction;
(function (Faction) {
    Faction["WARRIORS"] = "warriors";
    Faction["SAGES"] = "sages";
    Faction["EXPLORERS"] = "explorers";
    Faction["ROYAL_BLOOD"] = "royal_blood";
    Faction["SPECTRES"] = "spectres";
})(Faction || (Faction = {}));
/**
 * Convertit un UnifiedGenome en profil de personnalité.
 */
export function unifiedToPersonality(g) {
    const phen = g.getPhenotype();
    return {
        id: g.id,
        velocity: phen.exploration_rate ?? 0.5,
        precision: 1.0 - (phen.risk_tolerance ?? 0.5),
        dominance: phen.creativity_index ?? 0.5,
        empathy: phen.collaboration_drive ?? 0.5,
        stealth: 1.0 - (phen.exploration_rate ?? 0.5),
        skills: [],
        generation: g.generation,
        lineageId: g.factionId,
    };
}
/**
 * GENETIC-OPTIMIZER v2
 */
export class GeneticOptimizer {
    agentGenomes = new Map();
    constructor() {
        this.initializeGenomes();
    }
    initializeGenomes() {
        const defaultProfile = {
            velocity: 0.5, precision: 0.8, dominance: 0.5,
            empathy: 0.7, stealth: 0.5, skills: [], generation: 0,
        };
        this.agentGenomes.set('zeus', { ...defaultProfile, dominance: 1.0 });
        this.agentGenomes.set('athena', { ...defaultProfile, precision: 1.0 });
        this.agentGenomes.set('hydra_ui', { ...defaultProfile, velocity: 1.0, stealth: 0.8 });
        this.agentGenomes.set('erebus', { id: 'erebus', ...defaultProfile, precision: 0.9, stealth: 1.0, generation: 0 });
    }
    // ══════════════════════════════════════════════════════════
    // NOUVELLES MÉTHODES (Phase 2) — vrais UnifiedGenome
    // ══════════════════════════════════════════════════════════
    /**
     * Absorption d'un génome mort dans un survivant.
     * Vraie fusion : on transfère 1 gène aléatoire du mort vers le survivant,
     * puis on mute légèrement le survivant.
     */
    async absorbInto(survivor, victim) {
        if (!survivor || !victim)
            return;
        // Transférer 1 gène aléatoire du chromosome BEHAVIOR
        const victimGenes = victim.g_behavior;
        if (victimGenes.length === 0)
            return;
        const victimGene = victimGenes[Math.floor(Math.random() * victimGenes.length)];
        const survivorGenes = survivor.g_behavior;
        const survivorGene = survivorGenes[Math.floor(Math.random() * survivorGenes.length)];
        if (victimGene && survivorGene) {
            survivorGene.value = victimGene.value;
        }
        // Mutation légère post-fusion
        survivor.mutate(0.05);
        logger.debug(`[GENETIC] 🧬 ${survivor.id} absorbed gene from ${victim.id}`);
    }
    /**
     * Génère 2 héritiers (princes) à partir d'un chef et d'un partenaire.
     * Vrais UnifiedGenome, avec héritage par crossover + mutation.
     */
    generateHeirsFrom(chief, partner) {
        if (!chief || !partner)
            return [];
        logger.info(`[DYNASTY] 👑 Le Chef ${chief.id} engendre sa lignée avec ${partner.id}`);
        const heirs = [];
        for (let i = 0; i < 2; i++) {
            const heir = chief.crossover(partner);
            heir.agentName = `${chief.agentName}_heir_${i}_gen${chief.generation + 1}`;
            heir.generation = Math.max(chief.generation, partner.generation) + 1;
            heir.factionId = chief.factionId;
            heir.mutate(0.15);
            heirs.push(heir);
        }
        return heirs;
    }
    // ══════════════════════════════════════════════════════════
    // MÉTHODES LEGACY (rétro-compat)
    // ══════════════════════════════════════════════════════════
    /**
     * Génère 2 héritiers (profil de personnalité) à partir d'IDs de chefs.
     * @deprecated Utilisez `generateHeirsFrom(chief, partner)` avec de vrais génomes.
     */
    generateHeirs(chiefId, partnerId) {
        const chief = this.agentGenomes.get(chiefId);
        const partner = this.agentGenomes.get(partnerId);
        if (!chief || !partner)
            return [];
        logger.info(`[DYNASTY] 👑 Le Chef ${chiefId} engendre sa lignée avec ${partnerId}`);
        const heirs = [];
        for (let i = 0; i < 2; i++) {
            const heir = {
                velocity: (chief.velocity + partner.velocity) / 2 + (Math.random() - 0.5) * 0.1,
                precision: (chief.precision + partner.precision) / 2 + (Math.random() - 0.5) * 0.1,
                dominance: chief.dominance,
                empathy: partner.empathy,
                stealth: (chief.stealth + partner.stealth) / 2,
                skills: chief.skills.filter(s => s.isSealed).slice(0, 2),
                generation: chief.generation + 1,
                lineageId: chiefId,
            };
            heirs.push(heir);
        }
        return heirs;
    }
    /**
     * Élit un patron du Panthéon pour une faction.
     * @deprecated Fonctionne avec les PersonalityProfile, conservé pour rétro-compat.
     */
    electPatron(faction, averageGenome) {
        const scores = {
            athena: averageGenome.precision * 1.5 + averageGenome.velocity * 0.5,
            hermes: averageGenome.velocity * 1.5 + averageGenome.empathy * 0.5,
            zeus: averageGenome.dominance * 1.5 + averageGenome.precision * 0.5,
        };
        const elected = Object.entries(scores).reduce((a, b) => a[1] > b[1] ? a : b)[0];
        logger.info(`[GENETIC] 🗳️ La faction ${faction.toUpperCase()} a choisi son protecteur : ${elected.toUpperCase()}`);
        return elected;
    }
    /**
     * Applique une mutation CRISPR à une faction entière.
     * PHASE 2 : ne stub plus — utilise `mutateByStrategy` sur UnifiedGenome.
     * @param faction Faction cible (pour le logging)
     * @param trait Trait à muter (utilisé pour logging, ignoré par la mutation réelle)
     * @param intensity Intensité de la mutation
     * @param population Population cible (optionnel, défaut = [])
     */
    async mutateFaction(faction, trait, intensity, population = []) {
        logger.info(`[GENETIC] 🧬 Mutation CRISPR lancée sur la faction ${faction.toUpperCase()} (Trait: ${String(trait)}, intensité: ${intensity})`);
        let mutated = 0;
        for (const genome of population) {
            // Choisir la stratégie selon la faction
            const strategy = this.pickStrategyForFaction(faction);
            await genome.mutateByStrategy(Math.floor(Math.random() * genome.g_behavior.length), ChromosomeType.BEHAVIOR, strategy);
            mutated++;
        }
        logger.info(`[GENETIC] ✅ Mutation appliquée à ${mutated} génomes de la faction ${faction.toUpperCase()}.`);
        return { status: 'applied', count: mutated, faction };
    }
    pickStrategyForFaction(faction) {
        switch (faction) {
            case Faction.WARRIORS: return 'sacrifice'; // Altruisme guerrier
            case Faction.SAGES: return 'epigenetic'; // Sagesse = régulation
            case Faction.EXPLORERS: return 'transposon'; // Exploration = sauts
            case Faction.ROYAL_BLOOD: return 'bricolage'; // Noblesse = héritage
            case Faction.SPECTRES: return 'gaussian'; // Spectres = bruit
        }
    }
}
