/**
 * ═══════════════════════════════════════════════════════════════
 * FITNESS EVALUATOR — Calcule la fitness réelle d'un génome
 * ═══════════════════════════════════════════════════════════════
 *
 * La fitness n'est plus un chiffre arbitraire. Elle combine :
 * - Performance de l'agent dans sa dernière mission (40%)
 * - Satisfaction utilisateur estimée (30%)
 * - Efficacité des ressources (coût, latence) (20%)
 * - Pression évolutive (karma, ombre) (10%)
 *
 * Branché à ImperialCycle dans Phase 2.
 */

import type { UnifiedGenome } from './UnifiedGenome.js';

export interface HydraContext {
  /** Score de succès de la dernière mission (0-1). */
  taskSuccess: number;
  /** Satisfaction utilisateur dérivée (0-1). */
  userSatisfaction: number;
  /** Coût relatif (0 = gratuit, 1 = très cher). */
  costRatio: number;
  /** Latence relative (0 = instant, 1 = très lent). */
  latencyRatio: number;
  /** Pression évolutive (karma négatif ou stagnation). */
  evolutionaryPressure: number;
  /** Métadonnées additionnelles (optionnel). */
  metadata?: Record<string, unknown>;
}

export interface IFitnessEvaluator {
  evaluate(genome: UnifiedGenome, context?: HydraContext): number;
}

export const DEFAULT_FITNESS_WEIGHTS = {
  taskSuccess: 0.40,
  userSatisfaction: 0.30,
  costEfficiency: 0.20,
  evolutionaryPressure: 0.10,
} as const;

/**
 * Implémentation par défaut : combine les dimensions du contexte
 * avec un bonus pour les génomes équilibrés (entropie de Shannon des gènes).
 */
export class DefaultFitnessEvaluator implements IFitnessEvaluator {
  private weights = { ...DEFAULT_FITNESS_WEIGHTS };

  public evaluate(genome: UnifiedGenome, context?: HydraContext): number {
    // Si pas de contexte, retomber sur l'historique interne
    if (!context) {
      return this.fromHistory(genome);
    }

    const taskScore = Math.max(0, Math.min(1, context.taskSuccess));
    const userScore = Math.max(0, Math.min(1, context.userSatisfaction));
    const costScore = Math.max(0, Math.min(1, 1 - context.costRatio));  // bas coût = bon
    const latencyScore = Math.max(0, Math.min(1, 1 - context.latencyRatio));
    const efficiencyScore = (costScore + latencyScore) / 2;
    const pressureScore = Math.max(0, Math.min(1, context.evolutionaryPressure));

    const fitness =
      taskScore * this.weights.taskSuccess +
      userScore * this.weights.userSatisfaction +
      efficiencyScore * this.weights.costEfficiency +
      pressureScore * this.weights.evolutionaryPressure;

    return Math.max(0, Math.min(1, fitness));
  }

  /**
   * Fallback : fitness dérivée de l'historique et de la diversité génétique.
   */
  private fromHistory(genome: UnifiedGenome): number {
    if (genome.fitnessHistory.length === 0) return genome.fitness || 0.5;
    const recent = genome.fitnessHistory.slice(-10);
    const avg = recent.reduce((a, b) => a + b, 0) / recent.length;
    // Bonus de diversité : entropie des gènes du chromosome principal
    const diversityBonus = this.computeDiversityBonus(genome) * 0.05;
    return Math.max(0, Math.min(1, avg + diversityBonus));
  }

  /**
   * Entropie de Shannon normalisée des valeurs de gènes (0-1).
   * Une diversité élevée indique un génome "exploratoire".
   */
  private computeDiversityBonus(genome: UnifiedGenome): number {
    const sample = genome.g_behavior.slice(0, 50);
    if (sample.length === 0) return 0;
    const buckets = new Array(10).fill(0);
    for (const gene of sample) {
      const idx = Math.min(9, Math.floor(gene.value * 10));
      buckets[idx]++;
    }
    const total = sample.length;
    let entropy = 0;
    for (const count of buckets) {
      if (count > 0) {
        const p = count / total;
        entropy -= p * Math.log2(p);
      }
    }
    // Max entropy pour 10 buckets = log2(10) ≈ 3.32
    return entropy / Math.log2(10);
  }

  public getWeights(): typeof this.weights {
    return { ...this.weights };
  }
}
