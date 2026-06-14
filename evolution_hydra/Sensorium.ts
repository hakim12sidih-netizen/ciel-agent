import logger from '../utils/logger.js';
import type { PhiEngine } from './PhiEngine.js';
import { HardwareMetrics } from '../utils/HardwareMetrics.js';

export interface Qualia {
  id: string;
  source: string;
  intensity: number;
  feeling: 'COHERENT' | 'DISSONANT' | 'NEUTRAL';
}

/**
 * SENSORIUM — The Enaction Layer (Varela/Maturana).
 * Perception is not the reception of data but an active loop of structural 
 * coupling between the system and its environment.
 */
export class Sensorium {
  private phiEngine: PhiEngine;
  private qualiaInvariants: Map<string, Qualia> = new Map();
  private couplingStrength: number = 0.5;

  constructor(phiEngine: PhiEngine) {
    this.phiEngine = phiEngine;
    logger.info('[Sensorium] 👁️ Active Sensorium initialized. Enaction loop enabled.');
  }

  /**
   * Structural Coupling (Couplage Structurel).
   * Transforms raw environmental signals into Phenomenal Qualia 
   * based on the system's internal state (Φ).
   */
  enact(source: string, rawSignal: number) {
    const phi = this.phiEngine.getStatus().phi;
    const cDesc = this.phiEngine.getCausalDownwardPressure();

    // The feeling is an invariant of the interaction
    // Dissonance occurs when expectation (low energy) doesn't match signal
    const surprise = Math.abs(rawSignal - (phi / 2));
    const feeling = surprise > 0.8 ? 'DISSONANT' : (surprise < 0.2 ? 'COHERENT' : 'NEUTRAL');

    const intensity = rawSignal * (1 + cDesc);
    
    const qualia: Qualia = {
      id: `q_${Date.now()}`,
      source,
      intensity,
      feeling
    };

    this.qualiaInvariants.set(source, qualia);
    
    if (feeling === 'DISSONANT') {
      logger.warn(`[Sensorium] ⚡ DISSONANCE DETECTED in ${source}. Signal magnitude: ${intensity.toFixed(4)}`);
    } else if (feeling === 'COHERENT') {
      logger.debug(`[Sensorium] 💎 Coherent Qualia formed for ${source}.`);
    }

    // Structural coupling: Feedback into PhiEngine is done via external calls or integrated here
    // We feedback the "surprise" into the PhiEngine to minimize free energy in future cycles
  }

  /**
   * Hardware Enaction.
   * Couples the internal mind state directly to the hardware reality.
   */
  enactHard() {
    const cpu = HardwareMetrics.getRealCPULoad();
    const mem = HardwareMetrics.getRealMemoryUsage();
    this.enact('CPU_LOAD', cpu);
    this.enact('MEM_USAGE', mem);
  }

  /**
   * Intention-Guided Perception.
   * Perception is filtered by high-level "Attention".
   */
  getFilteredView(source: string): number {
    const q = this.qualiaInvariants.get(source);
    if (!q) return 0;

    // Direct Causal Downward pressure: The "will" to see modifies the intensity
    const attention = this.phiEngine.getCausalDownwardPressure();
    return q.intensity * (1 + attention);
  }

  /**
   * Autopoietic boundary maintenance.
   * The system defines its own limits through action.
   */
  updateBoundary() {
     const phi = this.phiEngine.getStatus().phi;
     // The coupling strength modulates how much the environment "penetrates" the system
     this.couplingStrength = Math.tanh(phi);
     
     // If PHI is low, we decrease coupling to protect operational closure (isolation)
     // If PHI is high, we increase coupling for active exploration (openness)
     logger.debug(`[Sensorium] 🌐 Structural Coupling Strength (Openness): ${this.couplingStrength.toFixed(4)}`);
  }
}
