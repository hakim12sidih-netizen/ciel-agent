/**
 * LOAD BALANCER - Équilibrage de charge & Routage intelligent
 * Distribue les requêtes aux agents basé sur charge et performance
 */

import logger from '../../utils/logger.js';
import { AgentProfiler } from '../profiling/AgentProfiler.js';

export interface LoadInfo {
  agentId: string;
  currentLoad: number;
  pendingRequests: number;
  avgLatency: number;
  healthScore: number; // 0-100
}

export type LoadBalancingStrategy = 'round_robin' | 'least_loaded' | 'best_performer' | 'adaptive';

/**
 * Équilibreur de charge pour les agents
 */
export class LoadBalancer {
  private agentQueues = new Map<string, number>();
  private roundRobinIndex = 0;
  private lastCheck = Date.now();
  private strategy: LoadBalancingStrategy = 'adaptive';

  constructor(
    private profiler: AgentProfiler,
    strategy?: LoadBalancingStrategy
  ) {
    if (strategy) {
      this.strategy = strategy;
    }
  }

  /**
   * Sélectionne un agent pour une requête
   */
  selectAgent(
    candidates: string[],
    priority: 'speed' | 'accuracy' | 'balanced' = 'balanced'
  ): string {
    if (candidates.length === 0) {
      throw new Error('No candidate agents available');
    }

    if (candidates.length === 1) {
      return candidates[0];
    }

    switch (this.strategy) {
      case 'round_robin':
        return this.selectRoundRobin(candidates);
      case 'least_loaded':
        return this.selectLeastLoaded(candidates);
      case 'best_performer':
        return this.selectBestPerformer(candidates);
      case 'adaptive':
      default:
        return this.selectAdaptive(candidates, priority);
    }
  }

  /**
   * Round Robin simple
   */
  private selectRoundRobin(candidates: string[]): string {
    const selected = candidates[this.roundRobinIndex % candidates.length];
    this.roundRobinIndex++;
    return selected;
  }

  /**
   * Sélectionne l'agent avec la charge minimale
   */
  private selectLeastLoaded(candidates: string[]): string {
    let bestAgent = candidates[0];
    let minLoad = this.agentQueues.get(candidates[0]) || 0;

    for (const agent of candidates) {
      const load = this.agentQueues.get(agent) || 0;
      if (load < minLoad) {
        minLoad = load;
        bestAgent = agent;
      }
    }

    return bestAgent;
  }

  /**
   * Sélectionne le meilleur agent (basé sur profiler)
   */
  private selectBestPerformer(candidates: string[]): string {
    return this.profiler.selectBestAgent(candidates) || candidates[0];
  }

  /**
   * Sélectionne adaptivement (combine charge + performance)
   */
  private selectAdaptive(
    candidates: string[],
    priority: 'speed' | 'accuracy' | 'balanced'
  ): string {
    const scored = candidates.map(agentId => {
      const profile = this.profiler.getProfile(agentId);
      const load = this.agentQueues.get(agentId) || 0;

      // Scorer basé sur profil + charge
      let score = 50; // Baseline

      if (profile) {
        const performanceWeight = 
          priority === 'accuracy' ? 0.7 :
          priority === 'speed' ? 0.5 :
          0.6;

        score = 
          profile.performanceScore * performanceWeight +
          (100 - Math.min(load * 10, 100)) * (1 - performanceWeight);
      } else {
        // Agent non-profilé : pénaliser si surcharge
        score = 100 - Math.min(load * 10, 100);
      }

      return { agentId, score, load };
    });

    scored.sort((a, b) => b.score - a.score);
    const selected = scored[0];

    logger.debug('[LOAD-BALANCER] Agent selected', {
      agent: selected.agentId,
      score: selected.score.toFixed(2),
      load: selected.load,
      strategy: this.strategy
    });

    return selected.agentId;
  }

  /**
   * Enregistre le début d'une exécution
   */
  startExecution(agentId: string) {
    const current = this.agentQueues.get(agentId) || 0;
    this.agentQueues.set(agentId, current + 1);
  }

  /**
   * Enregistre la fin d'une exécution
   */
  endExecution(agentId: string) {
    const current = this.agentQueues.get(agentId) || 0;
    this.agentQueues.set(agentId, Math.max(0, current - 1));
  }

  /**
   * Exécute une fonction avec tracking de charge
   */
  async executeWithTracking<T>(
    agent: string,
    fn: () => Promise<T>
  ): Promise<T> {
    this.startExecution(agent);
    try {
      return await fn();
    } finally {
      this.endExecution(agent);
    }
  }

  /**
   * Retourne les infos de charge de tous les agents
   */
  getLoadInfo(agents: string[]): LoadInfo[] {
    return agents.map(agentId => {
      const profile = this.profiler.getProfile(agentId);
      const pendingRequests = this.agentQueues.get(agentId) || 0;

      return {
        agentId,
        currentLoad: pendingRequests,
        pendingRequests,
        avgLatency: profile?.avgLatency || 0,
        healthScore: profile ? 
          Math.min(100, profile.performanceScore + (10 - pendingRequests * 2)) : 
          Math.max(0, 100 - pendingRequests * 10)
      };
    });
  }

  /**
   * Retourne l'agent avec la meilleure santé
   */
  getHealthiest(agents: string[]): string {
    const loadInfo = this.getLoadInfo(agents);
    return loadInfo.reduce((best, current) =>
      current.healthScore > best.healthScore ? current : best
    ).agentId;
  }

  /**
   * Change la stratégie d'équilibrage
   */
  setStrategy(strategy: LoadBalancingStrategy) {
    this.strategy = strategy;
    logger.info('[LOAD-BALANCER] Strategy changed', { strategy });
  }

  /**
   * Reset toutes les charges
   */
  reset() {
    this.agentQueues.clear();
  }
}

/**
 * Factory pour créer un load balancer avec singleton profiler
 */
export function createLoadBalancer(
  profiler: AgentProfiler,
  strategy?: LoadBalancingStrategy
): LoadBalancer {
  return new LoadBalancer(profiler, strategy);
}
