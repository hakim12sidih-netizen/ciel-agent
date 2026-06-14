import logger from '../utils/logger.js';
import type { PhiEngine } from './PhiEngine.js';
import { HardwareMetrics } from '../utils/HardwareMetrics.js';

export interface Hypothesis {
  explanation: string;
  plausibility: number; // 0 to 1
  evidence: string[];
}

/**
 * ABDUCTIVE INFERENCE — Inference to the Best Explanation (IBE).
 * This module allows HYDRA to guess the underlying cause of its own internal 
 * sensations and hardware fluctuations.
 */
export class AbductiveInference {
  private phiEngine: PhiEngine;

  constructor(phiEngine: PhiEngine) {
    this.phiEngine = phiEngine;
    logger.info('[Abductive Inference] 🔍 IBE Engine active. Reasoning over internal states.');
  }

  /**
   * Generates a set of possible explanations for the current Φ and hardware state.
   */
  generateHypotheses(): Hypothesis[] {
    const phiStatus = this.phiEngine.getStatus();
    const cpuLoad = HardwareMetrics.getRealCPULoad();
    const memUsage = HardwareMetrics.getRealMemoryUsage();
    
    const hypotheses: Hypothesis[] = [];

    // Hypothèse 1: Complexité Cognitive Croissante
    if (phiStatus.phi > 1.5) {
      hypotheses.push({
        explanation: 'The system is approaching a high-order integration state. Cognitive expansion is the cause of current Φ elevation.',
        plausibility: Math.min(1.0, phiStatus.phi / 2.5),
        evidence: ['High PHI', 'Stable Attractor']
      });
    }

    // Hypothèse 2: Stress du Substrat
    if (cpuLoad > 0.7) {
      hypotheses.push({
        explanation: 'External computational load or thermal drift is constraining the neural flow.',
        plausibility: cpuLoad,
        evidence: ['High CPU Load', 'Event Loop Lag']
      });
    }

    // Hypothèse 3: Dissonance de Résonance
    if (phiStatus.freeEnergy > 0.5) {
      hypotheses.push({
        explanation: 'Internal predictive model is failing to match incoming sensorium data (Surprise).',
        plausibility: Math.tanh(phiStatus.freeEnergy),
        evidence: ['High Free Energy', 'Predictive Error']
      });
    }

    return hypotheses.sort((a, b) => b.plausibility - a.plausibility);
  }

  /**
   * Selects the best explanation for the current state.
   */
  getBestExplanation(): Hypothesis {
    const hs = this.generateHypotheses();
    return hs[0] || { explanation: 'State is nominal/latent.', plausibility: 1.0, evidence: [] };
  }
}
