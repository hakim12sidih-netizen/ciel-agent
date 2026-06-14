import { HydraCore } from './HydraCore.js';
import { Faction } from '../../evolution/GeneticOptimizer.js';
import logger from '../../utils/logger.js';

/**
 * MISSION-ORCHESTRATOR v∞
 * Analyse les requêtes du Master et délègue aux factions.
 */
export class MissionOrchestrator {
  private lastTargetFaction: Faction = Faction.SAGES;
  constructor(private hydra: HydraCore) { }

  /**
   * Analyse une tâche et trouve la meilleure faction.
   */
  public async delegateTask(task: string) {
    logger.info(`[ORCHESTRATOR] 🧠 Analyse de la mission : "${task}"`);

    let targetFaction: Faction;
    let justification: string;

    if (task.toLowerCase().includes('code') || task.toLowerCase().includes('algorithme') || task.toLowerCase().includes('réflexion')) {
      targetFaction = Faction.SAGES;
      justification = "Capacités d'analyse et de précision supérieures.";
    } else if (task.toLowerCase().includes('attaque') || task.toLowerCase().includes('infiltration') || task.toLowerCase().includes('vitesse')) {
      targetFaction = Faction.WARRIORS;
      justification = "Vitesse d'exécution et dominance tactique.";
    } else {
      targetFaction = Faction.EXPLORERS;
      justification = "Capacité de récolte et de découverte de données.";
    }

    this.lastTargetFaction = targetFaction;
    logger.info(`[ORCHESTRATOR] 🎯 Faction sélectionnée : ${targetFaction.toUpperCase()} (${justification})`);

    // Envoi de l'ordre impérial
    await this.hydra.dispatchImperialOrder(targetFaction, task, "Greffe de module originel B-7");
  }

  public getLastTargetFaction(): Faction {
    return this.lastTargetFaction;
  }
}
