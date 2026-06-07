import logger from '../utils/logger.js';
import { systemBus } from '../core/SystemBus.js';
export class RLDaemon {
    ga;
    masterEngine;
    intervalMs;
    timer = null;
    isTesting = false;
    constructor(ga, masterEngine, intervalMs = 60000) {
        this.ga = ga;
        this.masterEngine = masterEngine;
        this.intervalMs = intervalMs;
    }
    start() {
        if (this.timer)
            return;
        logger.info(`[RL Daemon] Started. Will evaluate genomes every ${this.intervalMs / 1000}s of idle time.`);
        this.timer = setInterval(async () => {
            // Don't interrupt user operations or overlap tests
            if (this.masterEngine.isActive() || this.isTesting)
                return;
            const genome = this.ga.getUnevaluatedGenome();
            if (!genome) {
                // All evaluated, maybe wait for evolution
                return;
            }
            this.isTesting = true;
            systemBus.setStatus('LEARNING');
            try {
                logger.info(`[RL Daemon] 🧠 Benchmarking Genome ${genome.id} (Souveraineté Transendante)...`);
                // 1. Give it a polyglot challenge (OpenClaw style)
                const challenges = [
                    "Write a Rust function that computes the nth Fibonacci number and execute it.",
                    "Write a Python script that scrapes 'https://example.com' and prints the title.",
                    "Write a Go program that sorts an array of 100 random integers."
                ];
                const task = challenges[Math.floor(Math.random() * challenges.length)];
                const startTime = Date.now();
                // Build a temporary test engine with Transendance params
                const { QueryEngine } = await import('../core/QueryEngine.js');
                const testEngine = new QueryEngine({
                    provider: this.masterEngine.getProvider(),
                    model: this.masterEngine.getModel(),
                    temperature: genome.params.temperature,
                    systemPrompt: `RECURSIVE_TRANSCENDANCE | Target: OpenClaw Supremacy. ${genome.params.promptMutation}. 
           Preference: Isolated Execution (Docker/UniversalLab). Depth: ${genome.params.polyglotDepth}`,
                });
                // 2. Run simulation
                let result = '';
                let toolResults = [];
                let toolCallsCount = 0;
                let universalLabUsed = false;
                for await (const chunk of testEngine.query(task)) {
                    if (chunk.type === 'tool_call') {
                        toolCallsCount++;
                        if (chunk.toolCall?.function?.name === 'universal_lab')
                            universalLabUsed = true;
                    }
                    if (chunk.type === 'tool_result' && 'content' in chunk) {
                        toolResults.push(String(chunk.content ?? ''));
                    }
                    if (chunk.type === 'text')
                        result += chunk.content;
                }
                const durationMs = Date.now() - startTime;
                // 3. Compute Alpha-Fitness (Transcendance Level)
                let fitness = 0;
                // Success check (simplified heuristic: look for execution markers in tool results)
                const isSuccess = toolResults.some(r => r.includes('SUCCESS') || r.includes('out'));
                if (isSuccess)
                    fitness += 200;
                // Polyglot Bonus
                if (universalLabUsed) {
                    fitness += 150 * genome.params.polyglotDepth;
                }
                // Efficiency Bonus
                fitness += (100000 / durationMs);
                // Docker Synergy Bonus
                if (universalLabUsed && genome.params.dockerAffinity > 0.6) {
                    fitness += 50;
                }
                // 4. Report back
                this.ga.recordFitness(genome.id, 'TRANSENDANCE_AUDIT', fitness);
            }
            catch (err) {
                logger.error(`[RL Daemon] Test failed catastrophically: ${err.message}`);
                this.ga.recordFitness(genome.id, 'RL_DAEMON', 0); // Failed horribly
            }
            finally {
                this.isTesting = false;
                systemBus.setStatus('IDLE');
            }
        }, this.intervalMs);
    }
    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
}
