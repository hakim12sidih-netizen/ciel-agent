import type { QueryEngine } from '../core/QueryEngine.js';
import type { GeneticAlgorithm } from './GeneticAlgorithm.js';
import logger from '../utils/logger.js';
import { errorMessage } from '../types/index.js';
import { systemBus } from '../core/SystemBus.js';
import { scheduler } from '../polyglot/scheduler.js';

/**
 * RLDaemon — Reinforcement Learning autonomous genome benchmarking.
 *
 * Pass 11: Migrated from `setInterval` to the polyglot scheduler.
 */
export class RLDaemon {
  private ga: GeneticAlgorithm;
  private masterEngine: QueryEngine;
  private intervalMs: number;
  private unsubscribe: (() => void) | null = null;
  private isTesting = false;

  constructor(ga: GeneticAlgorithm, masterEngine: QueryEngine, intervalMs: number = 60000) {
    this.ga = ga;
    this.masterEngine = masterEngine;
    this.intervalMs = intervalMs;
  }

  async start() {
    if (this.unsubscribe) {
      throw new Error('[RL Daemon] already started');
    }
    logger.info(`[RL Daemon] Started. Will evaluate genomes every ${this.intervalMs / 1000}s of idle time.`);

    this.unsubscribe = await scheduler.schedule('rl_daemon', this.intervalMs, async () => {
      // Don't interrupt user operations or overlap tests
      if (this.masterEngine.isActive() || this.isTesting) return;

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
        let toolResults: string[] = [];
        let toolCallsCount = 0;
        let universalLabUsed = false;

         for await (const chunk of testEngine.query(task)) {
           if (chunk.type === 'tool_call') {
             toolCallsCount++;
             if (chunk.toolCall?.function?.name === 'universal_lab') universalLabUsed = true;
             if (chunk.content) toolResults.push(String(chunk.content));
           }
           if (chunk.type === 'text') result += chunk.content;
         }

        const durationMs = Date.now() - startTime;
        
        // 3. Compute Alpha-Fitness (Transcendance Level)
        let fitness = 0;
        
        // Success check (simplified heuristic: look for execution markers in tool results)
        const isSuccess = toolResults.some(r => r.includes('SUCCESS') || r.includes('out'));
        if (isSuccess) fitness += 200;

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

      } catch (err: unknown) {
        logger.error(`[RL Daemon] Test failed catastrophically: ${err.message}`);
        this.ga.recordFitness(genome.id, 'RL_DAEMON', 0); // Failed horribly
      } finally {
        this.isTesting = false;
        systemBus.setStatus('IDLE');
      }
    });
  }

  async stop() {
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null;
    }
  }
}
