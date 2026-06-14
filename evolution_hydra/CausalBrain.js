import logger from '../utils/logger.js';
export var NodeType;
(function (NodeType) {
    NodeType["ACTION"] = "action";
    NodeType["ENV"] = "environment";
    NodeType["OUTCOME"] = "outcome";
})(NodeType || (NodeType = {}));
/**
 * CausalBrain is the "What-If" engine for HYDRA.
 * It maps actions to consequences and allows the Council
 * to reason about counterfactuals using Pearl's Do-calculus concepts.
 */
export class CausalBrain {
    nodes = new Map();
    edges = [];
    engine;
    constructor(engine) {
        this.engine = engine;
        logger.info('[Causal Brain] 🧠 Structural Causal Model (SCM) initialized.');
    }
    registerEvent(id, type, description) {
        const node = { id, type, description, timestamp: Date.now() };
        this.nodes.set(id, node);
        logger.debug(`[Causal Brain] Event Registered: ${id} (${type})`);
    }
    createCausalLink(fromId, toId, strength = 0.5) {
        if (!this.nodes.has(fromId) || !this.nodes.has(toId))
            return;
        this.edges.push({ from: fromId, to: toId, strength });
        logger.debug(`[Causal Brain] Link Established: ${fromId} ➔ ${toId} (strength: ${strength})`);
    }
    /**
     * Performs an "Imaginary Intervention" (Intervention Do(X)).
     * Asks the engine to reason about what would happen if a specific action WAS NOT taken.
     */
    async counterfactualReasoning(targetActionId, desiredOutcome) {
        const action = this.nodes.get(targetActionId);
        if (!action)
            return 'Action not found in causal map.';
        logger.info(`[Causal Brain] 🌀 Reasoning over counterfactual: What if ${targetActionId} never happened?`);
        const context = Array.from(this.nodes.values())
            .filter(n => n.timestamp < action.timestamp)
            .map(n => `- ${n.type}: ${n.description}`)
            .join('\n');
        const prompt = `System state before target action:\n${context}\n\n
                    Target Action that occurred: ${action.description}\n\n
                    Question: If I had NOT performed this action, what would be the most likely alternative outcome concerning "${desiredOutcome}"? 
                    Reason using structural causal inference.`;
        let reasoning = '';
        for await (const chunk of this.engine.query(prompt)) {
            if (chunk.type === 'text')
                reasoning += chunk.content;
        }
        return reasoning;
    }
    getGraph() {
        return { nodes: Array.from(this.nodes.values()), edges: this.edges };
    }
}
