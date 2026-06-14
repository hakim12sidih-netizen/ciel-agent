/**
 * AGENT PROFILER - Profilage des performances des agents
 * Optimise le routage basé sur les performances historiques
 */

import logger from '../../utils/logger.js';

export interface AgentProfile {
  agentId: string;
  avgLatency: number;
  successRate: number;
  failureRate: number;
  totalExecutions: number;
  lastUsed: number;
  specialty: string;
  performanceScore: number; // 0-100
}

export interface ProfileStats {
  totalAgents: number;
  avgLatency: number;
  avgSuccessRate: number;
  topPerformer: AgentProfile | null;
  profiles: AgentProfile[];
}

/**
 * Profile les performances des agents
 */
export class AgentProfiler {
  private profiles = new Map<string, {
    avgLatency: number;
    successCount: number;
    failureCount: number;
    totalExecutions: number;
    lastUsed: number;
    specialty: string;
  }>();

  /**
   * Enregistre l'exécution d'un agent
   */
  recordExecution(
    agentId: string,
    latency: number,
    success: boolean,
    specialty: string = 'general'
  ) {
    const profile = this.profiles.get(agentId) || {
      avgLatency: 0,
      successCount: 0,
      failureCount: 0,
      totalExecutions: 0,
      lastUsed: 0,
      specialty
    };

    profile.totalExecutions++;
    profile.avgLatency = 
      (profile.avgLatency * (profile.totalExecutions - 1) + latency) / 
      profile.totalExecutions;

    if (success) {
      profile.successCount++;
    } else {
      profile.failureCount++;
    }

    profile.lastUsed = Date.now();

    this.profiles.set(agentId, profile);

    logger.debug('[PROFILER] Agent execution recorded', {
      agentId,
      latency: latency.toFixed(2) + 'ms',
      success,
      totalExecutions: profile.totalExecutions
    });
  }

  /**
   * Sélectionne le meilleur agent parmi une liste (basé sur performance)
   */
  selectBestAgent(candidates: string[]): string | null {
    if (candidates.length === 0) return null;
    if (candidates.length === 1) return candidates[0];

    // Calculer le score pour chaque candidat
    const scored = candidates.map(agentId => ({
      agentId,
      score: this.calculateScore(agentId)
    }));

    // Trier par score décroissant
    scored.sort((a, b) => b.score - a.score);

    logger.debug('[PROFILER] Agent selection', {
      selected: scored[0].agentId,
      score: scored[0].score.toFixed(2),
      alternatives: scored.slice(1, 3).map(s => s.agentId)
    });

    return scored[0].agentId;
  }

  /**
   * Calcule le score de performance (0-100)
   */
  private calculateScore(agentId: string): number {
    const profile = this.profiles.get(agentId);
    if (!profile || profile.totalExecutions === 0) {
      return 50; // Score neutre pour agents non profilés
    }

    const successRate = 
      (profile.successCount / profile.totalExecutions) * 100;
    const latencyScore = Math.max(0, 100 - (profile.avgLatency / 10));
    const consistencyBonus = Math.min(10, profile.totalExecutions / 10);

    return (
      successRate * 0.6 +           // 60% succès
      latencyScore * 0.3 +          // 30% latence
      consistencyBonus * 0.1        // 10% bonus consistance
    );
  }

  /**
   * Retourne le profil d'un agent
   */
  getProfile(agentId: string): AgentProfile | null {
    const profile = this.profiles.get(agentId);
    if (!profile) return null;

    return {
      agentId,
      avgLatency: profile.avgLatency,
      successRate: (profile.successCount / profile.totalExecutions) * 100,
      failureRate: (profile.failureCount / profile.totalExecutions) * 100,
      totalExecutions: profile.totalExecutions,
      lastUsed: profile.lastUsed,
      specialty: profile.specialty,
      performanceScore: this.calculateScore(agentId)
    };
  }

  /**
   * Retourne les statistiques globales
   */
  getStats(): ProfileStats {
    const profiles = Array.from(this.profiles.entries())
      .map(([agentId, profile]) => ({
        agentId,
        ...profile,
        successRate: (profile.successCount / profile.totalExecutions) * 100,
        failureRate: (profile.failureCount / profile.totalExecutions) * 100,
        performanceScore: this.calculateScore(agentId)
      }))
      .sort((a, b) => b.performanceScore - a.performanceScore);

    const avgLatency = profiles.length > 0
      ? profiles.reduce((sum, p) => sum + p.avgLatency, 0) / profiles.length
      : 0;

    const avgSuccessRate = profiles.length > 0
      ? profiles.reduce((sum, p) => sum + p.successRate, 0) / profiles.length
      : 100;

    return {
      totalAgents: profiles.length,
      avgLatency,
      avgSuccessRate,
      topPerformer: profiles[0] || null,
      profiles
    };
  }

  /**
   * Reset le profil d'un agent
   */
  resetProfile(agentId: string) {
    this.profiles.delete(agentId);
  }

  /**
   * Reset tous les profils
   */
  resetAll() {
    this.profiles.clear();
  }

  /**
   * Retourne les agents avec mauvaise performance
   */
  getUnderperformers(threshold: number = 50): AgentProfile[] {
    const stats = this.getStats();
    return stats.profiles.filter(p => p.performanceScore < threshold);
  }
}

/**
 * Instance globale singleton
 */
export const globalProfiler = new AgentProfiler();
