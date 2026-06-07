import { formatTokenCount, estimateCost } from '../utils/tokenizer.js';
import { COST_PER_MILLION_TOKENS } from '../config/defaults.js';

export interface UsageSnapshot {
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  estimatedCost: number;
  model: string;
  requestCount: number;
}

export class CostTracker {
  private inputTokens = 0;
  private outputTokens = 0;
  private requestCount = 0;
  private model: string;
  private history: Array<{ timestamp: Date; input: number; output: number; model: string }> = [];

  constructor(model: string = 'llama3.1') {
    this.model = model;
  }

  addUsage(inputTokens: number, outputTokens: number, model?: string) {
    this.inputTokens += inputTokens;
    this.outputTokens += outputTokens;
    this.requestCount++;
    this.history.push({ timestamp: new Date(), input: inputTokens, output: outputTokens, model: model || this.model });
  }

  setModel(model: string) { this.model = model; }

  getSnapshot(): UsageSnapshot {
    const costs = COST_PER_MILLION_TOKENS[this.model] || { input: 0, output: 0 };
    return {
      inputTokens: this.inputTokens,
      outputTokens: this.outputTokens,
      totalTokens: this.inputTokens + this.outputTokens,
      estimatedCost: estimateCost(this.inputTokens, this.outputTokens, costs),
      model: this.model,
      requestCount: this.requestCount,
    };
  }

  getFormattedUsage(): string {
    const snap = this.getSnapshot();
    const cost = snap.estimatedCost > 0 ? ` ($${snap.estimatedCost.toFixed(4)})` : ' (free)';
    return `${formatTokenCount(snap.totalTokens)} tokens${cost} · ${snap.requestCount} req`;
  }

  reset() {
    this.inputTokens = 0;
    this.outputTokens = 0;
    this.requestCount = 0;
    this.history = [];
  }
}
