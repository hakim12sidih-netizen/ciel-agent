/**
 * METRICS COLLECTOR - Observabilité & Monitoring Complète
 * Collecte: latence, taux de réussite, usage agents, erreurs, mémoire
 */

import logger from '../../utils/logger.js';
import { scheduler } from '../../polyglot/scheduler.js';

export interface AgentMetrics {
  invocations: number;
  totalLatency: number;
  avgLatency: number;
  successCount: number;
  failureCount: number;
  successRate: number;
  lastUsed: number;
}

export interface SystemMetrics {
  requestCount: number;
  totalLatency: number;
  avgLatency: number;
  successRate: number;
  memoryUsage: number;
  uptime: number;
  nvmAccessCount: number;
  tokenizedCount: number;
  agentMetrics: Map<string, AgentMetrics>;
  errorCounts: Map<string, number>;
}

/**
 * Collecte et agrège les métriques du système
 */
export class MetricsCollector {
  private metrics: SystemMetrics = {
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

  private readonly flushInterval = 60000; // 1 minute

  constructor() {
    this.startAutoFlush();
  }

  /**
   * Enregistre une requête
   */
  recordRequest(
    latency: number,
    agent: string,
    success: boolean,
    tokensProcessed = 0
  ) {
    this.metrics.requestCount++;
    this.metrics.totalLatency += latency;
    this.metrics.avgLatency = this.metrics.totalLatency / this.metrics.requestCount;
    this.metrics.tokenizedCount += tokensProcessed;

    // Mise à jour du taux de réussite
    const successCount = Math.floor(
      this.metrics.requestCount * (this.metrics.successRate / 100)
    );
    const newSuccessCount = success ? successCount + 1 : successCount;
    this.metrics.successRate = (newSuccessCount / this.metrics.requestCount) * 100;

    // Mise à jour des métriques d'agent
    this.updateAgentMetrics(agent, latency, success);
  }

  /**
   * Enregistre un accès NVM
   */
  recordNvmAccess(latency: number) {
    this.metrics.nvmAccessCount++;
  }

  /**
   * Met à jour les métriques d'un agent
   */
  private updateAgentMetrics(agent: string, latency: number, success: boolean) {
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

    const agentMetrics = this.metrics.agentMetrics.get(agent)!;
    agentMetrics.invocations++;
    agentMetrics.totalLatency += latency;
    agentMetrics.avgLatency = agentMetrics.totalLatency / agentMetrics.invocations;

    if (success) {
      agentMetrics.successCount++;
    } else {
      agentMetrics.failureCount++;
    }

    agentMetrics.successRate = 
      (agentMetrics.successCount / agentMetrics.invocations) * 100;
    agentMetrics.lastUsed = Date.now();
  }

  /**
   * Enregistre une erreur
   */
  recordError(agentId: string, errorType: string) {
    const count = this.metrics.errorCounts.get(errorType) || 0;
    this.metrics.errorCounts.set(errorType, count + 1);
  }

  /**
   * Retourne un snapshot des métriques actuelles
   */
  getMetrics(): SystemMetrics {
    return {
      ...this.metrics,
      memoryUsage: process.memoryUsage().heapUsed / 1024 / 1024, // MB
      uptime: Date.now() - this.metrics.uptime
    };
  }

  /**
   * Retourne les métriques d'un agent spécifique
   */
  getAgentMetrics(agentId: string): AgentMetrics | undefined {
    return this.metrics.agentMetrics.get(agentId);
  }

  /**
   * Retourne l'agent le plus performant
   */
  getTopAgent(): [string, AgentMetrics] | undefined {
    if (this.metrics.agentMetrics.size === 0) return undefined;

    let topAgent: [string, AgentMetrics] | undefined;
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
  private async flush() {
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
   * Démarre le flush automatique des métriques (via polyglot scheduler)
   */
  private startAutoFlush() {
    scheduler.schedule('metrics_collector_flush', this.flushInterval, () => this.flush())
      .catch((e) => {
        logger.warn(`[MetricsCollector] scheduler.schedule failed, using raw setInterval: ${e instanceof Error ? e.message : e}`);
        setInterval(() => this.flush(), this.flushInterval);
      });
  }

  /**
   * Formate le temps de fonctionnement
   */
  private formatUptime(ms: number): string {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }
}

/**
 * Instance globale singleton
 */
export const globalMetrics = new MetricsCollector();
