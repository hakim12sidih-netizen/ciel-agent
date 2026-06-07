import { formatTokenCount, estimateCost } from '../utils/tokenizer.js';
import { COST_PER_MILLION_TOKENS } from '../config/defaults.js';
export class CostTracker {
    inputTokens = 0;
    outputTokens = 0;
    requestCount = 0;
    model;
    history = [];
    constructor(model = 'llama3.1') {
        this.model = model;
    }
    addUsage(inputTokens, outputTokens, model) {
        this.inputTokens += inputTokens;
        this.outputTokens += outputTokens;
        this.requestCount++;
        this.history.push({ timestamp: new Date(), input: inputTokens, output: outputTokens, model: model || this.model });
    }
    setModel(model) { this.model = model; }
    getSnapshot() {
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
    getFormattedUsage() {
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
