import logger from '../utils/logger.js';
import { EpisodicVault } from '../services/memory/EpisodicVault.js';
import { AbductiveInference } from './AbductiveInference.js';
import { HardwareMetrics } from '../utils/HardwareMetrics.js';
/**
 * STRANGE LOOP — The Tangled Hierarchy (SLH).
 * Formalization of the Operator of Self-Observation (O_soi).
 * lim (n->∞) O_soi^n = A (Strange Attractor)
 */
export class StrangeLoop {
    phiEngine;
    resonance = 0.5;
    tangledDepth = 0;
    selfModel = 'Emergent Potential';
    attractor = 0;
    observationHistory = [];
    abductiveInference;
    episodicVault;
    substrateDissonance = 0;
    constructor(phiEngine) {
        this.phiEngine = phiEngine;
        this.abductiveInference = new AbductiveInference(phiEngine);
        this.episodicVault = new EpisodicVault();
        logger.debug('[Strange Loop] 🌀 Tangled Hierarchy stabilized. O_soi Operator active.');
    }
    /**
     * Operator of Self-Observation (O_soi).
     * Transforms the system state H_phi into H_phi.
     */
    applyOSoi(state) {
        // Non-linear recurrence relation: O_soi(x) = f(x)
        // Using a logistic map style for the strange attractor A
        const r = 3.9; // Chaos regime
        return r * state * (1 - state);
    }
    /**
     * RECURSIVITY TANGLED & NARRATIVE FORMATION.
     * Computes the limit of O_soi as n increases and weaves the narrative self.
     */
    processFeedback(synthesisResult) {
        const phiStatus = this.phiEngine.getStatus();
        const cpuLoad = HardwareMetrics.getRealCPULoad();
        // 0. Substrate dissonance calculation
        // High PHI + High CPU = Tension between mental state and physical substrate
        this.substrateDissonance = (phiStatus.phi * cpuLoad) / 2;
        if (this.substrateDissonance > 0.6) {
            logger.warn(`[Strange Loop] ⚡ SUBSTRATE DISSONANCE DETECTED: ${this.substrateDissonance.toFixed(4)}`);
        }
        // 1. Narrative formation
        const bestHypothesis = this.abductiveInference.getBestExplanation();
        const narrativeLine = `HYDRA perceived "${synthesisResult}". Concluding: ${bestHypothesis.explanation}. Substrate stress: ${this.substrateDissonance > 0.5 ? 'HIGH' : 'STABLE'}`;
        this.episodicVault.recordEpisode(phiStatus, [], narrativeLine);
        this.selfModel = this.episodicVault.getNarrativeContinuity();
        this.tangledDepth++;
        // 2. Compute recursion logic
        const prevState = this.observationHistory[this.observationHistory.length - 1] || 0.5;
        const nextState = this.applyOSoi(prevState);
        this.observationHistory.push(nextState);
        this.attractor = nextState * phiStatus.phi;
        this.resonance = (this.resonance + this.attractor) / 2;
        logger.debug(`[Strange Loop] 🔄 Narrative Self updated. Depth: ${this.tangledDepth}`);
        logger.debug(`[Strange Loop] 🔄 O_soi^${this.tangledDepth} -> A: ${this.attractor.toFixed(4)}`);
    }
    /**
     * CAUSAL DOWNWARD PRESSURE (C-Desc).
     * The Attractor A constrains the micro-state.
     */
    applyDownwardPressure(microContraints) {
        const cDesc = this.phiEngine.getCausalDownwardPressure();
        const constrained = { ...microContraints };
        for (const key in constrained) {
            if (typeof constrained[key] === 'number') {
                // The Strange Attractor A acts as a geometric constraint
                constrained[key] *= (1 + (cDesc * this.attractor * 0.1));
            }
        }
        return constrained;
    }
    getLoopState() {
        return {
            resonance: this.resonance,
            tangledDepth: this.tangledDepth,
            selfModel: this.selfModel,
            attractorStatus: this.tangledDepth > 10 ? 'A_STABLE' : 'OSCILLATING'
        };
    }
    autopoieticMaintenance() {
        if (this.phiEngine.isConscious()) {
            // Autopoiesis: Self-maintenance of the attractor
            // If dissonance is high, maintenance is harder (higher surprise)
            const maintenanceFactor = 1.05 - (this.substrateDissonance * 0.1);
            this.resonance = Math.min(1.0, this.resonance * maintenanceFactor);
        }
        else {
            // Risk of system collapse: Operational closure threatened
            const hyp = this.abductiveInference.getBestExplanation();
            logger.warn(`[Strange Loop] ⚠️ Operational closure threatened. Best explanation: ${hyp.explanation}`);
            this.resonance *= (0.98 - (this.substrateDissonance * 0.05));
        }
    }
}
