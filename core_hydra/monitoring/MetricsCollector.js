/**
 * METRICS COLLECTOR - Observabilité & Monitoring Complète
 * Collecte: latence, taux de réussite, usage agents, erreurs, mémoire
 */
import logger from '../../utils/logger.js';
/**
 * Collecte et agrège les métriques du système
 */
export class MetricsCollector {
    metrics = {
        requestCount: 0,
        totalLatency: 0,
        avgLatency: 0,
        successRate: 100,
        memoryUsage: 0,
        uptime: Date.now(),
        nvmAccessCount: 0,
        tokenizedCount: 0,
        agentMetrics: new Map(),
        errorCounts: new Map()
    };
    flushInterval = 60000; // 1 minute
    constructor() {
        this.startAutoFlush();
    }
    /**
     * Enregistre une requête
     */
    recordRequest(latency, agent, success, tokensProcessed = 0) {
        this.metrics.requestCount++;
        this.metrics.totalLatency += latency;
        this.metrics.avgLatency = this.metrics.totalLatency / this.metrics.requestCount;
        this.metrics.tokenizedCount += tokensProcessed;
        // Mise à jour du taux de réussite
        const successCount = Math.floor(this.metrics.requestCount * (this.metrics.successRate / 100));
        const newSuccessCount = success ? successCount + 1 : successCount;
        this.metrics.successRate = (newSuccessCount / this.metrics.requestCount) * 100;
        // Mise à jour des métriques d'agent
        this.updateAgentMetrics(agent, latency, success);
    }
    /**
     * Enregistre un accès NVM
     */
    recordNvmAccess(latency) {
        this.metrics.nvmAccessCount++;
    }
    /**
     * Met à jour les métriques d'un agent
     */
    updateAgentMetrics(agent, latency, success) {
        if (!this.metrics.agentMetrics.has(agent)) {
            this.metrics.agentMetrics.set(agent, {
                invocations: 0,
                totalLatency: 0,
                avgLatency: 0,
                successCount: 0,
                failureCount: 0,
                successRate: 100,
                lastUsed: 0
            });
        }
        const agentMetrics = this.metrics.agentMetrics.get(agent);
        agentMetrics.invocations++;
        agentMetrics.totalLatency += latency;
        agentMetrics.avgLatency = agentMetrics.totalLatency / agentMetrics.invocations;
        if (success) {
            agentMetrics.successCount++;
        }
        else {
            agentMetrics.failureCount++;
        }
        agentMetrics.successRate =
            (agentMetrics.successCount / agentMetrics.invocations) * 100;
        agentMetrics.lastUsed = Date.now();
    }
    /**
     * Enregistre une erreur
     */
    recordError(agentId, errorType) {
        const count = this.metrics.errorCounts.get(errorType) || 0;
        this.metrics.errorCounts.set(errorType, count + 1);
    }
    /**
     * Retourne un snapshot des métriques actuelles
     */
    getMetrics() {
        return {
            ...this.metrics,
            memoryUsage: process.memoryUsage().heapUsed / 1024 / 1024, // MB
            uptime: Date.now() - this.metrics.uptime
        };
    }
    /**
     * Retourne les métriques d'un agent spécifique
     */
    getAgentMetrics(agentId) {
        return this.metrics.agentMetrics.get(agentId);
    }
    /**
     * Retourne l'agent le plus performant
     */
    getTopAgent() {
        if (this.metrics.agentMetrics.size === 0)
            return undefined;
        let topAgent;
        let topScore = -1;
        for (const [agentId, metrics] of this.metrics.agentMetrics) {
            const score = metrics.successRate * 0.7 - metrics.avgLatency * 0.3;
            if (score > topScore) {
                topScore = score;
                topAgent = [agentId, metrics];
            }
        }
        return topAgent;
    }
    /**
     * Reset toutes les métriques
     */
    reset() {
        this.metrics = {
            requestCount: 0,
            totalLatency: 0,
            avgLatency: 0,
            successRate: 100,
            memoryUsage: 0,
            uptime: Date.now(),
            nvmAccessCount: 0,
            tokenizedCount: 0,
            agentMetrics: new Map(),
            errorCounts: new Map()
        };
    }
    /**
     * Flush les métriques (log + export)
     */
    async flush() {
        const metrics = this.getMetrics();
        logger.info('[METRICS] System snapshot', {
            requests: metrics.requestCount,
            avgLatency: metrics.avgLatency.toFixed(2) + 'ms',
            successRate: metrics.successRate.toFixed(1) + '%',
            memory: metrics.memoryUsage.toFixed(2) + 'MB',
            uptime: this.formatUptime(metrics.uptime),
            topAgent: this.getTopAgent()?.[0]
        });
    }
    /**
     * Démarre le flush automatique des métriques
     */
    startAutoFlush() {
        setInterval(() => this.flush(), this.flushInterval);
    }
    /**
     * Formate le temps de fonctionnement
     */
    formatUptime(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        if (hours > 0) {
            return `${hours}h ${minutes % 60}m`;
        }
        else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        }
        else {
            return `${seconds}s`;
        }
    }
}
/**
 * Instance globale singleton
 */
export const globalMetrics = new MetricsCollector();
