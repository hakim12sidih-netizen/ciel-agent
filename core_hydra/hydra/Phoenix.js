import * as fs from 'fs/promises';
import * as path from 'path';
import logger from '../../utils/logger.js';
/**
 * PROTOCOLE PHOENIX — Résilience Absolue
 * Implémente les 4 stratégies anti-abandon.
 */
export class PhoenixProtocol {
    failureStore = [];
    failurePath;
    skillGraph;
    constructor(skillGraph, titanDir = `${process.env.USERPROFILE ?? '~'}/.titan`) {
        this.skillGraph = skillGraph;
        this.failurePath = path.join(titanDir, 'failures');
        this.loadFailures().catch(e => logger.warn(`[PHOENIX] Impossible de charger les échecs: ${e.message}`));
    }
    async loadFailures() {
        try {
            await fs.mkdir(this.failurePath, { recursive: true });
            const files = await fs.readdir(this.failurePath);
            for (const file of files) {
                if (!file.endsWith('.json'))
                    continue;
                const data = await fs.readFile(path.join(this.failurePath, file), 'utf-8');
                this.failureStore.push(JSON.parse(data));
            }
            logger.info(`[PHOENIX] 📖 ${this.failureStore.length} archives d'échec chargées.`);
        }
        catch {
            logger.info(`[PHOENIX] 📖 Aucun échec précédent trouvé.`);
        }
    }
    getFailures() {
        return this.failureStore;
    }
    /**
     * STRATÉGIE 1 — Dégradation Gracieuse
     * Renvoie le prochain agent de fallback si l'agent principal échoue.
     */
    getFallbackAgent(failedAgentId) {
        const fallbackMap = {
            hephaistos: 'athena',
            athena: 'zeus',
            artemis: 'athena',
            tethys: 'poseidon',
            apollon: 'zeus',
            dionysos: 'hydra_ui',
            poseidon: 'zeus',
            hades: 'zeus',
            hermes: 'zeus',
            // Gen 2/3 extensions
            janus: 'zeus',
            moirae: 'athena',
            pandore: 'dionysos',
            tartare: 'hades',
            chronos: 'zeus',
            thanatos: 'hades',
            hypnos: 'dionysos',
            morbius: 'hephaistos',
            eris: 'zeus',
            nemesis: 'athena'
        };
        const fallback = fallbackMap[failedAgentId] ?? 'zeus';
        logger.warn(`[PHOENIX] 🔥 Agent ${failedAgentId} failed → Falling back to ${fallback}`);
        return fallback;
    }
    /**
     * STRATÉGIE 2 — Multi-Passes Créatives
     * Retourne la stratégie à utiliser selon le numéro de tentative.
     */
    getPassStrategy(attempt) {
        const strategies = [
            'standard',
            'alternative',
            'hybrid',
            'out_of_box',
            'brute_force',
            'creative_emergence',
        ];
        return strategies[Math.min(attempt, strategies.length - 1)];
    }
    /**
     * STRATÉGIE 3 — Apprentissage par l'Échec
     * Enregistre l'échec, génère un "vaccin", et crée un nouveau nœud anti-échec.
     */
    async recordFailure(input, error) {
        const record = {
            id: `failure_${Date.now()}`,
            timestamp: Date.now(),
            input,
            errorType: error.name,
            errorMessage: error.message,
            vaccine: `AVOID: ${error.name} when processing "${input.substring(0, 50)}"`,
            resolved: false,
        };
        this.failureStore.push(record);
        // Create anti-failure node in the skill graph
        const newNodeId = this.skillGraph.addAntiFailureNode(`anti_${error.name.toLowerCase()}`);
        logger.info(`[PHOENIX] 🧬 Anti-failure node N${newNodeId} created for: ${error.name}`);
        // Persist failure asynchronously
        this.persistFailure(record).catch(() => { });
        return record;
    }
    async persistFailure(record) {
        try {
            await fs.mkdir(this.failurePath, { recursive: true });
            const filePath = path.join(this.failurePath, `${record.id}.json`);
            await fs.writeFile(filePath, JSON.stringify(record, null, 2), 'utf-8');
        }
        catch {
            // Silently ignore
        }
    }
    async resolveFailure(id) {
        const record = this.failureStore.find(f => f.id === id);
        if (!record)
            return false;
        record.resolved = true;
        await this.persistFailure(record);
        logger.info(`[PHOENIX] 🩹 Échec ${id} résolu avec succès.`);
        return true;
    }
    getStats() {
        const total = this.failureStore.length;
        const resolved = this.failureStore.filter(f => f.resolved).length;
        return {
            total_failures: total,
            resolved_failures: resolved,
            resolution_rate: total > 0 ? (resolved / total) * 100 : 100
        };
    }
    /**
     * STRATÉGIE 4 — Redondance Fantôme
     * Compare deux résultats d'agents et retourne le meilleur (ou déclenche APOLLON).
     */
    compareResults(resultA, resultB) {
        const divergence = resultA.confidence < 0.7 && resultB.confidence < 0.7;
        if (resultA.confidence >= resultB.confidence) {
            return { winner: resultA.agentId, content: resultA.content, divergence };
        }
        return { winner: resultB.agentId, content: resultB.content, divergence };
    }
    getFailureStats() {
        return {
            total: this.failureStore.length,
            unresolved: this.failureStore.filter((f) => !f.resolved).length,
        };
    }
}
