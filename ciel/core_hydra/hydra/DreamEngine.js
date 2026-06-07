import logger from '../../utils/logger.js';
import { TelegramNotifier } from '../../utils/TelegramNotifier.js';
import { errorMessage } from '../../types/index.js';
/**
 * DREAM-ENGINE v∞.DREAM
 * Moteur d'auto-entraînement et de Self-Play pour HYDRA-BRAIN.
 */
export class DreamEngine {
    brain;
    core;
    isDreaming = false;
    constructor(brain, core) {
        this.brain = brain;
        this.core = core;
    }
    /**
     * Déclenche un cycle complet de Rêve Lucide (Auto-entraînement)
     */
    async startDreamCycle(durationMinutes = 60) {
        if (this.isDreaming)
            return;
        this.isDreaming = true;
        logger.info(`[DREAM-ENGINE] 🌙 Début du cycle de Rêve Lucide (${durationMinutes} min).`);
        logger.info("[DREAM-ENGINE] 🧩 Mode Self-Play activé : HYDRA va générer ses propres données.");
        const endTime = Date.now() + durationMinutes * 60 * 1000;
        let iterations = 0;
        while (Date.now() < endTime) {
            iterations++;
            await this.runSelfPlayIteration(iterations);
            // Pause courte entre les rêves pour ne pas saturer le CPU
            await new Promise(r => setTimeout(r, 5000));
        }
        this.isDreaming = false;
        logger.info(`[DREAM-ENGINE] ✨ Cycle de rêve terminé. ${iterations} itérations d'apprentissage effectuées.`);
        try {
            // Consolidation nocturne
            const hippocampus = this.brain.getHippocampus();
            if (hippocampus && typeof hippocampus.consolidate === 'function') {
                hippocampus.consolidate();
            }
            // Notification
            await TelegramNotifier.notify(`🌙 Cycle de rêve terminé. Itérations: ${iterations}`);
        }
        catch (e) {
            logger.debug(`[DREAM-ENGINE] Notification ou consolidation ignorée: ${errorMessage(e)}`);
        }
    }
    /**
     * Une itération de Self-Play
     */
    async runSelfPlayIteration(idx) {
        logger.debug(`[DREAM-ENGINE] 🌀 Itération de rêve #${idx}...`);
        // 1. Génération d'un défi (Challenge Generation)
        const challenge = this.generateChallenge();
        logger.debug(`[DREAM-ENGINE] 🎯 Défi auto-généré : "${challenge}"`);
        // 2. Résolution via le Cœur Hydra (Débat des 21 agents)
        const result = await this.core.processRequest(challenge);
        // 3. Évaluation (Self-Correction)
        const success = result.success && result.consensusReached;
        // 4. Apprentissage (Backpropagation simulée)
        await this.brain.onlineLearn({ challenge, result }, success);
        if (success) {
            logger.debug(`[DREAM-ENGINE] ✅ Apprentissage réussi pour l'itération #${idx}.`);
        }
        else {
            logger.warn(`[DREAM-ENGINE] ❌ Échec de l'itération #${idx} : Analyse de l'erreur en cours...`);
        }
    }
    generateChallenge() {
        const phoenix = this.core.phoenix;
        if (phoenix && typeof phoenix.getFailures === 'function') {
            const failures = phoenix.getFailures();
            if (failures && failures.length > 0) {
                // Curriculum basé sur les faiblesses récentes
                const target = failures[Math.floor(Math.random() * Math.min(failures.length, 5))];
                return `[AUTO-CURRICULUM] Résoudre le problème lié à la mission échouée: "${target.mission}" (Erreur: ${target.error})`;
            }
        }
        const categories = [
            "Optimisation de code Rust pour TITAN-NVM",
            "Détection de vulnérabilités dans un protocole réseau",
            "Simulation d'une attaque de type Sybil sur le SpiderWeb",
            "Amélioration de la compression Zstd pour la couche L4",
            "Rédaction d'une épopée mythologique sur la naissance de Proteus",
            "Architecture distribuée: concevoir un consensus sans leader",
            "Implémentation d'un RAG multimodal",
            "Sécurisation d'un smart contract Solidity"
        ];
        return categories[Math.floor(Math.random() * categories.length)];
    }
    getStatus() {
        return {
            is_dreaming: this.isDreaming,
            engine: "DreamEngine v∞",
            mode: "Self-Play / Auto-Curriculum"
        };
    }
}
