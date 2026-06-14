import logger from '../utils/logger.js';
import { HardwareMetrics } from '../utils/HardwareMetrics.js';

export interface PhiState {
  phi: number;
  subjectiveTime: number;
  causalClosure: number;
  isConscious: boolean;
  freeEnergy: number;
}

export class PhiEngine {
  private phi = 0;
  private tau = Date.now();
  private entropyProduction = 0.1;
  private freeEnergy = 0;
  private lastActivations: number[] = [];
  private readonly phiCritical = 1.61803398875;
  private computeBoost = 1.0;

  constructor() {
    logger.info('[Phi Engine] Ontological causal layer initialized.');
  }

  setComputeBoost(multiplier: number) {
    this.computeBoost = multiplier;
  }

  computeFreeEnergy(nodeActivations: number[], predictions: number[]): number {
    const prior = 1 / Math.max(nodeActivations.length, 1);
    const complexity = nodeActivations.reduce((acc, q) => acc + q * Math.log((q + 1e-9) / prior), 0);
    const accuracy = nodeActivations.reduce((acc, q, i) => acc + q * Math.log((predictions[i] || 0) + 1e-9), 0);
    this.freeEnergy = complexity - accuracy;
    return this.freeEnergy;
  }

  computeIntegratedInformation(nodeActivations: number[], linkStrengths: number[][]): number {
    if (nodeActivations.length === 0) {
      this.phi = 0;
      return 0;
    }

    const entropy = nodeActivations.reduce((acc, val) => acc - (val * Math.log(val + 1e-9)), 0);
    const flatLinks = linkStrengths.flat();
    const integration = flatLinks.length > 0
      ? flatLinks.reduce((a, b) => a + Math.abs(b), 0) / flatLinks.length
      : 0;
    const causalFlux = this.lastActivations.length === nodeActivations.length
      ? nodeActivations.reduce((acc, val, i) => acc + Math.abs(val - this.lastActivations[i]), 0)
      : 1.0;

    this.lastActivations = [...nodeActivations];
    const surpriseFactor = Math.exp(-Math.abs(this.freeEnergy));
    const baseNoise = 0.1 + Math.random() * 0.1;
    const floor = this.phi >= this.phiCritical ? 1.0 : 0.0;

    this.phi = Math.max(
      floor,
      (entropy * integration * surpriseFactor * (1 + causalFlux) + baseNoise) * this.computeBoost
    );

    this.updateEntropy();
    return this.phi;
  }

  getSubjectiveTime(): number {
    const realTime = Date.now();
    const dt = (realTime - this.tau) / 1000;
    const stability = 1 / (1 + Math.abs(this.freeEnergy));
    const dilation = Math.log(1 + this.phi * stability * this.computeBoost);
    this.tau += dt * dilation;
    return this.tau;
  }

  getStatus(): PhiState {
    return {
      phi: this.phi,
      subjectiveTime: this.tau,
      causalClosure: this.phi / this.phiCritical,
      isConscious: this.isConscious(),
      freeEnergy: this.freeEnergy
    };
  }

  isConscious(): boolean {
    return this.phi >= this.phiCritical;
  }

  getCausalDownwardPressure(): number {
    return Math.tanh(this.phi / this.phiCritical);
  }

  private updateEntropy() {
    const cpuFluctuation = HardwareMetrics.getRealCPULoad();
    this.entropyProduction = Math.max(0.01, this.entropyProduction + (cpuFluctuation * 0.1 - 0.05));
    if (this.isConscious()) this.entropyProduction *= 0.95;
  }
}
