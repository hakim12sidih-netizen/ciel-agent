/**
 * ThoughtTree.ts
 *
 * Cognitive Workflow Phase 8: Advanced Reasoning Strategies
 * - Chain-of-Thought (CoT): Step-by-step reasoning
 * - Tree-of-Thought (ToT): Explore multiple paths
 * - Monte Carlo Tree Search (MCTS): Balance exploration/exploitation
 * - Process Reward Model: Score reasoning quality (o1/DeepSeek-R1 foundation)
 */
// ============================================================================
// PROCESS REWARD MODEL: Score reasoning steps quality
// ============================================================================
export class ProcessRewardModel {
    /**
     * Score the quality of a reasoning step.
     * Based on: clarity, logical flow, evidence, brevity
     */
    scoreStep(step, context, targetGoal) {
        let score = 0.5; // Base score
        // Clarity check (0-0.2)
        if (!step.includes('?') && step.length > 20 && step.length < 500) {
            score += 0.15;
        }
        // Logical flow check (0-0.2)
        if (step.includes('therefore') || step.includes('because') ||
            step.includes('implies') || step.includes('resulted')) {
            score += 0.15;
        }
        // Evidence quality (0-0.2)
        if (step.includes('data') || step.includes('study') || step.includes('evidence') ||
            step.includes('observed') || step.includes('measured')) {
            score += 0.15;
        }
        // Progress toward goal (0-0.2)
        if (targetGoal && step.toLowerCase().includes(targetGoal.toLowerCase())) {
            score += 0.15;
        }
        // Brevity bonus (0-0.1)
        if (step.length < 300) {
            score += 0.1;
        }
        // Penalty for uncertainty without justification
        if (step.includes('maybe') || step.includes('perhaps') || step.includes('uncertain')) {
            score -= 0.1;
        }
        return Math.max(0, Math.min(1, score));
    }
    /**
     * Score entire reasoning chain quality
     */
    scoreChain(steps, targetGoal) {
        if (steps.length === 0)
            return 0;
        const stepScores = steps.map((step, idx) => {
            const progress = idx / steps.length; // Later steps contribute more
            return this.scoreStep(step, steps.slice(0, idx).join(' '), targetGoal) * (0.5 + 0.5 * progress);
        });
        const avgScore = stepScores.reduce((a, b) => a + b, 0) / stepScores.length;
        // Bonus for conciseness (fewer steps is better, if complete)
        const conciseness = Math.max(0, 1 - steps.length / 10);
        return (avgScore * 0.9) + (conciseness * 0.1);
    }
    /**
     * Identify weak steps in reasoning chain
     */
    findWeakSteps(steps, targetGoal) {
        return steps
            .map((step, idx) => ({
            step,
            score: this.scoreStep(step, steps.slice(0, idx).join(' '), targetGoal),
            suggestion: this.suggestImprovement(step)
        }))
            .filter(item => item.score < 0.5)
            .sort((a, b) => a.score - b.score);
    }
    suggestImprovement(step) {
        if (!step.includes('because') && !step.includes('therefore')) {
            return 'Add logical connector: "therefore", "because", "implies"';
        }
        if (step.length > 500) {
            return 'Simplify: Break into smaller substeps';
        }
        if (step.includes('maybe') || step.includes('uncertain')) {
            return 'Justify uncertainty: "Research suggests..." or "Evidence indicates..."';
        }
        return 'Consider adding supporting evidence or data';
    }
}
// ============================================================================
// CHAIN-OF-THOUGHT: Step-by-step decomposition
// ============================================================================
export class ChainOfThought {
    rewardModel;
    constructor() {
        this.rewardModel = new ProcessRewardModel();
    }
    /**
     * Generate step-by-step reasoning chain
     */
    generateChain(question, context) {
        const steps = [];
        let reasoning = `Chain-of-Thought for: "${question}"\n\n`;
        // Step 1: Restate problem
        steps.push(`Clarifying the question: What exactly is being asked? "${question}"`);
        reasoning += `Step 1: ${steps[0]}\n`;
        // Step 2: Break down
        steps.push("Breaking down into subproblems: What are the key components?");
        reasoning += `Step 2: ${steps[1]}\n`;
        // Step 3: Identify constraints
        steps.push("Identifying relevant information and constraints from context");
        if (context) {
            reasoning += `Context: ${context}\n`;
        }
        // Step 4: Reason forward
        steps.push("Applying relevant principles or rules to the subproblems");
        reasoning += `Step 4: ${steps[3]}\n`;
        // Step 5: Integrate
        steps.push("Combining intermediate results toward final answer");
        reasoning += `Step 5: ${steps[4]}\n`;
        const chainScore = this.rewardModel.scoreChain(steps, question);
        const finalAnswer = "Integration of above reasoning leads to conclusion";
        return {
            question,
            steps,
            finalAnswer,
            reasoning,
            confidence: chainScore
        };
    }
    /**
     * Self-correct during chain generation
     */
    generateChainWithCorrection(question, maxAttempts = 3) {
        let best = null;
        let bestScore = 0;
        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            const result = this.generateChain(question);
            const score = this.rewardModel.scoreChain(result.steps, question);
            if (score > bestScore) {
                bestScore = score;
                best = result;
            }
            // Attempt to improve
            if (attempt < maxAttempts - 1) {
                const weak = this.rewardModel.findWeakSteps(result.steps, question);
                if (weak.length > 0) {
                    // Try reformulating weakest step
                    result.steps[result.steps.findIndex(s => s === weak[0].step)] =
                        `[REVISED] ${weak[0].suggestion}`;
                }
            }
        }
        return best;
    }
}
// ============================================================================
// TREE-OF-THOUGHT: Explore multiple reasoning paths
// ============================================================================
export class TreeOfThought {
    rewardModel;
    nodes = new Map();
    nodeCounter = 0;
    constructor() {
        this.rewardModel = new ProcessRewardModel();
    }
    /**
     * Generate and explore tree of alternative reasoning paths
     */
    generateTree(question, branchingFactor = 3, depth = 3) {
        this.nodes.clear();
        this.nodeCounter = 0;
        const rootId = this.createNode(question, 0);
        this.explore(rootId, depth, branchingFactor);
        // Find best path
        const bestPath = this.findBestPath();
        const bestScore = this.getPathScore(bestPath);
        const exploredPaths = this.countPaths();
        return {
            question,
            tree: this.nodes,
            bestPath,
            bestScore,
            exploredPaths
        };
    }
    /**
     * Recursively explore reasoning tree
     */
    explore(nodeId, remainingDepth, branchingFactor) {
        if (remainingDepth === 0)
            return;
        const currentNode = this.nodes.get(nodeId);
        const branches = [];
        // Generate alternative reasoning paths
        for (let i = 0; i < branchingFactor; i++) {
            const branchContent = `Alternative approach ${i + 1} for: ${currentNode.content}`;
            const branchId = this.createNode(branchContent, currentNode.depth + 1, nodeId);
            branches.push(branchId);
            // Score this branch
            const score = this.rewardModel.scoreStep(branchContent, currentNode.content, currentNode.content);
            const node = this.nodes.get(branchId);
            node.score = score;
            // Recursively explore
            this.explore(branchId, remainingDepth - 1, Math.max(1, branchingFactor - 1));
        }
        currentNode.children = branches;
    }
    /**
     * Create tree node
     */
    createNode(content, depth, parent) {
        const id = `node_${this.nodeCounter++}`;
        this.nodes.set(id, {
            id,
            content,
            depth,
            parent,
            score: 0,
            visits: 0
        });
        return id;
    }
    /**
     * Find best reasoning path using depth-first search with scoring
     */
    findBestPath() {
        if (this.nodes.size === 0)
            return [];
        const root = Array.from(this.nodes.values()).find(n => !n.parent);
        if (!root)
            return [];
        let best = [root.id];
        let bestScore = root.score || 0;
        const dfs = (nodeId, path, score) => {
            if (!this.nodes.get(nodeId)?.children || this.nodes.get(nodeId).children.length === 0) {
                if (score > bestScore) {
                    bestScore = score;
                    best = [...path];
                }
                return;
            }
            for (const childId of this.nodes.get(nodeId).children) {
                const childScore = this.nodes.get(childId).score || 0;
                dfs(childId, [...path, childId], score + childScore);
            }
        };
        dfs(root.id, [root.id], bestScore);
        return best;
    }
    /**
     * Calculate path score
     */
    getPathScore(path) {
        return path.reduce((sum, id) => {
            const node = this.nodes.get(id);
            return sum + (node?.score || 0);
        }, 0) / Math.max(1, path.length);
    }
    /**
     * Count total explored paths
     */
    countPaths() {
        let count = 0;
        const dfs = (nodeId) => {
            const node = this.nodes.get(nodeId);
            if (!node?.children || node.children.length === 0) {
                count++;
                return;
            }
            for (const childId of node.children) {
                dfs(childId);
            }
        };
        const root = Array.from(this.nodes.values()).find(n => !n.parent);
        if (root)
            dfs(root.id);
        return count;
    }
    /**
     * Visualize tree structure
     */
    visualize() {
        let output = '';
        const visited = new Set();
        const dfs = (nodeId, indent) => {
            if (visited.has(nodeId))
                return;
            visited.add(nodeId);
            const node = this.nodes.get(nodeId);
            output += `${indent}├─ [${node.score?.toFixed(2)}] ${node.content.substring(0, 60)}...\n`;
            if (node.children) {
                for (const childId of node.children) {
                    dfs(childId, indent + '  ');
                }
            }
        };
        const root = Array.from(this.nodes.values()).find(n => !n.parent);
        if (root)
            dfs(root.id, '');
        return output;
    }
}
// ============================================================================
// MONTE CARLO TREE SEARCH: Exploration/Exploitation balance
// ============================================================================
export class MonteCarloTreeSearch {
    rewardModel;
    nodes = new Map();
    nodeCounter = 0;
    ucbConstant = 1.41; // sqrt(2)
    constructor() {
        this.rewardModel = new ProcessRewardModel();
    }
    /**
     * Run MCTS for planning optimal sequence of reasoning steps
     */
    run(problem, iterations = 100) {
        this.nodes.clear();
        this.nodeCounter = 0;
        const rootId = this._createNode(problem);
        for (let i = 0; i < iterations; i++) {
            // Selection & Expansion
            let nodeId = this.select(rootId);
            // Simulation
            const reward = this.simulate(nodeId);
            // Backpropagation
            this.backpropagate(nodeId, reward);
        }
        const bestPath = this.getBestPath(rootId);
        const winRate = bestPath.length > 0 ?
            (this.nodes.get(bestPath[bestPath.length - 1]).reward || 0) : 0;
        return {
            question: problem,
            iterations,
            bestPlan: bestPath,
            winRate: Math.max(0, Math.min(1, winRate)),
            confidence: Math.min(1, bestPath.length / 5) // Longer plans = higher confidence
        };
    }
    /**
     * Selection phase: Use UCB1 to balance exploration/exploitation
     */
    select(nodeId) {
        const node = this.nodes.get(nodeId);
        // If not fully explored, expand
        if (!node.children || node.children.length < 3) {
            return this.expandNode(nodeId);
        }
        // UCB1: Upper Confidence Bound
        let best = node.children[0];
        let bestScore = -Infinity;
        for (const childId of node.children) {
            const child = this.nodes.get(childId);
            const exploitation = (child.reward || 0) / Math.max(1, child.visits || 1);
            const exploration = Math.sqrt(Math.log(node.visits || 1) / Math.max(1, child.visits || 1));
            const ucb = exploitation + this.ucbConstant * exploration;
            if (ucb > bestScore) {
                bestScore = ucb;
                best = childId;
            }
        }
        return this.select(best); // Recurse
    }
    /**
     * Expand node: Add child nodes (alternative plans)
     */
    expandNode(nodeId) {
        const node = this.nodes.get(nodeId);
        if (!node.children)
            node.children = [];
        const newChild = this._createNode(`Step ${node.children.length + 1}`, nodeId);
        node.children.push(newChild);
        return newChild;
    }
    _createNode(content, parent) {
        const id = `node_${this.nodeCounter++}`;
        this.nodes.set(id, {
            id,
            content,
            depth: (this.nodes.get(parent)?.depth ?? -1) + 1,
            parent,
            score: 0,
            visits: 0
        });
        return id;
    }
    /**
     * Simulation: Random playout to estimate node value
     */
    simulate(nodeId) {
        // Simple heuristic: simulate path quality
        let score = 0.5;
        let current = nodeId;
        for (let step = 0; step < 5; step++) {
            const node = this.nodes.get(current);
            if (!node)
                break;
            score += this.rewardModel.scoreStep(node.content, '', '') * (1 - step * 0.1);
            if (node.children && node.children.length > 0) {
                current = node.children[Math.floor(Math.random() * node.children.length)];
            }
            else {
                break;
            }
        }
        return Math.max(0, Math.min(1, score));
    }
    /**
     * Backpropagation: Update all ancestors with reward
     */
    backpropagate(nodeId, reward) {
        let current = nodeId;
        while (current) {
            const node = this.nodes.get(current);
            node.visits = (node.visits || 0) + 1;
            node.reward = ((node.reward || 0) * (node.visits - 1) + reward) / node.visits;
            current = node.parent;
        }
    }
    /**
     * Get best path found
     */
    getBestPath(nodeId) {
        const node = this.nodes.get(nodeId);
        if (!node.children || node.children.length === 0) {
            return [nodeId];
        }
        let best = node.children[0];
        let bestReward = this.nodes.get(best).reward || 0;
        for (const childId of node.children) {
            const reward = this.nodes.get(childId).reward || 0;
            if (reward > bestReward) {
                bestReward = reward;
                best = childId;
            }
        }
        return [nodeId, ...this.getBestPath(best)];
    }
    /**
     * Create node
     */
    createNode(content, parent) {
        const id = `mcts_${this.nodeCounter++}`;
        this.nodes.set(id, {
            id,
            content,
            depth: 0,
            parent,
            visits: 0,
            reward: 0
        });
        return id;
    }
}
// ============================================================================
// THOUGHT ENGINE: Coordinator
// ============================================================================
export class ThoughtEngine {
    chain;
    tree;
    mcts;
    rewardModel;
    constructor() {
        this.chain = new ChainOfThought();
        this.tree = new TreeOfThought();
        this.mcts = new MonteCarloTreeSearch();
        this.rewardModel = new ProcessRewardModel();
    }
    /**
     * Generate reasoning in 3 modes: Fast (CoT), Balanced (ToT), Deep (MCTS)
     */
    thinkMode(question, mode = 'balanced') {
        const start = Date.now();
        let result;
        switch (mode) {
            case 'fast':
                result = this.chain.generateChain(question);
                break;
            case 'balanced':
                result = this.tree.generateTree(question, 2, 2);
                break;
            case 'deep':
                result = this.mcts.run(question, 50);
                break;
        }
        return {
            mode,
            result,
            timing: Date.now() - start
        };
    }
    /**
     * Adaptive thinking: Chooses mode based on problem complexity
     */
    adaptiveThink(question) {
        const complexity = this.estimateComplexity(question);
        if (complexity < 0.4) {
            return this.thinkMode(question, 'fast');
        }
        else if (complexity < 0.7) {
            return this.thinkMode(question, 'balanced');
        }
        else {
            return this.thinkMode(question, 'deep');
        }
    }
    /**
     * Estimate problem complexity
     */
    estimateComplexity(question) {
        let score = 0.3;
        if (question.includes('how') || question.includes('why'))
            score += 0.2;
        if (question.includes('and') && question.length > 100)
            score += 0.2;
        if (question.includes('trade-off') || question.includes('versus'))
            score += 0.2;
        return Math.min(1, score);
    }
    /**
     * Meta-reasoning: Reflect on own reasoning
     */
    reflect(reasoning) {
        if ('steps' in reasoning) {
            const weak = this.rewardModel.findWeakSteps(reasoning.steps, reasoning.question);
            if (weak.length > 0) {
                return `Weak points detected: ${weak.map(w => w.suggestion).join('; ')}`;
            }
        }
        return 'Reasoning appears sound';
    }
}
export default ThoughtEngine;
