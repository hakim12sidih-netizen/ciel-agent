import logger from '../utils/logger.js';
import { TorchRLBridge } from './TorchRLBridge.js';
export class TitanRL {
    rewardWeights = new Array(12).fill(1 / 12);
    bridge = null;
    useBridge = false;
    constructor(bridgeOptions) {
        logger.info('[Titan-RL] 🧠 Moteur de Reinforcement Learning à 12 Dimensions initialisé.');
        if (bridgeOptions) {
            this.bridge = new TorchRLBridge(bridgeOptions);
            this.useBridge = true;
            logger.info(`[Titan-RL] 🌉 Bridge enabled: ${bridgeOptions.trainerPath ?? 'default'}`);
        }
    }
    /**
     * Calcule le vecteur de récompense 12D pour une action
     */
    compute12DReward(result) {
        const reward = new Array(12).fill(0);
        // r1: Réussite
        reward[0] = result.success ? 1.0 : -1.0;
        // r2: Efficacité
        reward[1] = result.efficiency;
        // r3: Créativité
        reward[2] = result.novelty;
        // r4: Robustesse
        reward[3] = 1.0 - result.error_rate;
        // r5: Frugalité
        reward[4] = Math.max(0, 1.0 - (result.ram_used / 8000));
        // r6: Vitesse
        reward[5] = Math.max(0, 1.0 - (result.time / 10));
        // r7: Autonomie
        reward[6] = Math.max(0, 1.0 - (result.user_interventions / 5));
        // r8: Symbiose
        reward[7] = Math.min(1.0, result.helped_agents / 3);
        // r9: Curiosité
        reward[8] = Math.min(1.0, result.states_explored / 100);
        // r10: Sécurité
        reward[9] = result.safe ? 1.0 : -1.0;
        // r11: Évolution (Placeholder)
        reward[10] = result.success && result.novelty > 0.8 ? 1.0 : 0.0;
        // r12: Plaisir (estimation)
        reward[11] = result.user_satisfaction;
        return reward.map(r => Math.max(-1, Math.min(1, r))); // Clamp -1 to 1
    }
    /**
     * PHASE 5 : applique l'apprentissage au génome.
     * Si un bridge est configuré, délègue au trainer Python (vrai policy gradient).
     * Sinon, utilise la somme pondérée legacy.
     */
    async learn(genome, taskResult) {
        const rewardVector = this.compute12DReward(taskResult);
        let totalFitness;
        let policyUpdated = false;
        if (this.useBridge && this.bridge) {
            // PHASE 5 : vrai policy gradient via Python
            const state = this.computeStateVector(genome, taskResult);
            const result = await this.bridge.trainStep(state, rewardVector);
            if (result.status !== 'error') {
                policyUpdated = true;
                // Recalculer la fitness avec la nouvelle policy
                totalFitness = this.fitnessFromAction(result.action, rewardVector);
            }
            else {
                // Fallback sur la logique legacy
                totalFitness = this.legacyFitness(rewardVector);
            }
        }
        else {
            totalFitness = this.legacyFitness(rewardVector);
        }
        // Bonus/Malus (legacy)
        if (rewardVector[2] > 0.8 && rewardVector[0] === 1) {
            totalFitness += 0.2;
        }
        totalFitness = Math.max(0, Math.min(1, (totalFitness + 1) / 2));
        genome.fitnessHistory.push(totalFitness);
        // Meta-RL: adapter les poids si les échecs s'accumulent
        if (genome.fitnessHistory.length > 10) {
            this.adaptRewardWeights(genome.fitnessHistory.slice(-10));
        }
        if (policyUpdated) {
            logger.debug(`[Titan-RL] 🌉 Policy updated via bridge, fitness=${totalFitness.toFixed(3)}`);
        }
        return totalFitness;
    }
    /**
     * Variante synchrone pour rétro-compatibilité.
     * Si bridge est configuré, attend la Promise et log un warning.
     */
    learnSync(genome, taskResult) {
        if (this.useBridge) {
            logger.warn('[Titan-RL] ⚠️ learnSync called but bridge is async. Use learn() instead.');
        }
        const rewardVector = this.compute12DReward(taskResult);
        return this.legacyFitness(rewardVector);
    }
    /**
     * Construit le vecteur d'état 12D à partir du génome + résultat.
     * [last_fitness, fitness_std, episode_count, success_rate, ...]
     */
    computeStateVector(genome, taskResult) {
        const history = genome.fitnessHistory;
        const last = history.length > 0 ? history[history.length - 1] : 0.5;
        const mean = history.length > 0 ? history.reduce((a, b) => a + b, 0) / history.length : 0.5;
        const variance = history.length > 1
            ? history.reduce((acc, v) => acc + Math.pow(v - mean, 2), 0) / history.length
            : 0;
        const std = Math.sqrt(variance);
        return [
            last, // 0: fitness récente
            std, // 1: stabilité
            Math.min(1, history.length / 100), // 2: expérience
            taskResult.success ? 1 : 0, // 3: succès
            taskResult.efficiency, // 4: efficacité
            1.0 - taskResult.error_rate, // 5: robustesse
            Math.max(0, 1.0 - taskResult.time / 10), // 6: vitesse
            taskResult.safe ? 1 : 0, // 7: sécurité
            taskResult.novelty, // 8: nouveauté
            Math.min(1, taskResult.states_explored / 100), // 9: exploration
            taskResult.user_satisfaction, // 10: satisfaction
            Math.min(1, taskResult.helped_agents / 3), // 11: symbiose
        ];
    }
    /**
     * Calcule la fitness depuis l'action de la policy (dot product avec reward).
     */
    fitnessFromAction(action, reward) {
        if (!action || action.length !== 12)
            return 0;
        let total = 0;
        for (let i = 0; i < 12; i++) {
            total += action[i] * reward[i];
        }
        return total;
    }
    /**
     * Fitness legacy (somme pondérée fixe).
     */
    legacyFitness(rewardVector) {
        let total = 0;
        for (let i = 0; i < 12; i++) {
            total += rewardVector[i] * this.rewardWeights[i];
        }
        return total;
    }
    adaptRewardWeights(recentHistory) {
        const avgFitness = recentHistory.reduce((a, b) => a + b, 0) / recentHistory.length;
        // Si la fitness est faible, prioriser la sécurité et l'efficacité sur la créativité
        if (avgFitness < 0.4) {
            this.rewardWeights[9] *= 1.2; // Security
            this.rewardWeights[0] *= 1.2; // Success
            this.rewardWeights[2] *= 0.8; // Creativity
        }
        else {
            // Sinon on peut prioriser l'exploration et la vitesse
            this.rewardWeights[2] *= 1.1; // Creativity
            this.rewardWeights[8] *= 1.1; // Curiosity
        }
        // Normalize
        const sum = this.rewardWeights.reduce((a, b) => a + b, 0);
        this.rewardWeights = this.rewardWeights.map(w => w / sum);
    }
    /**
     * PHASE 5 : accès au bridge pour monitoring.
     */
    getBridge() {
        return this.bridge;
    }
    isUsingBridge() {
        return this.useBridge;
    }
}
// ============================================================
// MÉMOIRE ÉPISODIQUE HIÉRARCHIQUE (MEH)
// ============================================================
export class HierarchicalEpisodicMemory {
    micro = []; // 100ms-1s
    mini = []; // 1s-10s
    mega = []; // 10s-5min
    epic = []; // 5min+
    constructor() {
        logger.info('[MEH] 🧠 Hippocampe Artificiel initialisé.');
    }
    storeMicro(state, action, reward, nextState) {
        this.micro.push({
            state, action, reward, next: nextState, timestamp: Date.now()
        });
        if (this.micro.length > 10000)
            this.micro.shift(); // Max 10000
    }
    consolidate() {
        // Micro → Mini
        if (this.micro.length > 100) {
            const sequence = this.micro.slice(-100);
            this.mini.push({
                type: 'mini',
                duration: sequence[sequence.length - 1].timestamp - sequence[0].timestamp,
                total_reward: sequence.reduce((acc, s) => acc + s.reward[0], 0),
                state_start: sequence[0].state,
                state_end: sequence[sequence.length - 1].next
            });
            this.micro = [];
            if (this.mini.length > 5000)
                this.mini.shift();
        }
        // Mini → Mega
        if (this.mini.length > 50) {
            const episode = this.mini.slice(-50);
            this.mega.push({
                type: 'mega',
                subgoals_achieved: episode.filter(m => m.total_reward > 0).length,
            });
            this.mini = [];
            if (this.mega.length > 1000)
                this.mega.shift();
        }
        // Mega → Epic
        if (this.mega.length > 20) {
            this.epic.push({
                type: 'epic',
                lesson: 'Consolidated lesson from 20 mega episodes',
                applicability: 0.85
            });
            this.mega = [];
            if (this.epic.length > 100)
                this.epic.shift();
        }
    }
}
