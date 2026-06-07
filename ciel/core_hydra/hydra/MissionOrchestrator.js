import { Faction } from '../../evolution/GeneticOptimizer.js';
import logger from '../../utils/logger.js';
/**
 * MISSION-ORCHESTRATOR v∞
 * Analyse les requêtes du Master et délègue aux factions.
 */
export class MissionOrchestrator {
    hydra;
    lastTargetFaction = Faction.SAGES;
    constructor(hydra) {
        this.hydra = hydra;
    }
    /**
     * Analyse une tâche et trouve la meilleure faction.
     */
    async delegateTask(task) {
        logger.info(`[ORCHESTRATOR] 🧠 Analyse de la mission : "${task}"`);
        let targetFaction;
        let justification;
        if (task.toLowerCase().includes('code') || task.toLowerCase().includes('algorithme') || task.toLowerCase().includes('réflexion')) {
            targetFaction = Faction.SAGES;
            justification = "Capacités d'analyse et de précision supérieures.";
        }
        else if (task.toLowerCase().includes('attaque') || task.toLowerCase().includes('infiltration') || task.toLowerCase().includes('vitesse')) {
            targetFaction = Faction.WARRIORS;
            justification = "Vitesse d'exécution et dominance tactique.";
        }
        else {
            targetFaction = Faction.EXPLORERS;
            justification = "Capacité de récolte et de découverte de données.";
        }
        this.lastTargetFaction = targetFaction;
        logger.info(`[ORCHESTRATOR] 🎯 Faction sélectionnée : ${targetFaction.toUpperCase()} (${justification})`);
        // Envoi de l'ordre impérial
        await this.hydra.dispatchImperialOrder(targetFaction, task, "Greffe de module originel B-7");
    }
    getLastTargetFaction() {
        return this.lastTargetFaction;
    }
}
