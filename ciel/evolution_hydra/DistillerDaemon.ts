import { GroqProvider } from '../providers/GroqProvider.js';
import { DataFactory } from '../council/training/DataFactory.js';
import { systemBus } from '../core/SystemBus.js';
import logger from '../utils/logger.js';
import { errorMessage } from '../types/index.js';
import { scheduler } from '../polyglot/scheduler.js';

/**
 * DISTILLER DAEMON — The Knowledge Forge of HYDRA.
 * This service autonomously consults the Cloud Oracle to generate
 * training data (distillation) for the local PyTorch brain.
 *
 * Pass 11: Migrated from `setInterval` to the polyglot scheduler.
 */
export class DistillerDaemon {
  private oracle: GroqProvider | null = null;
  private factory: DataFactory;
  private unsubscribe: (() => void) | null = null;
  private initialTimeout: NodeJS.Timeout | null = null;
  private isDistilling = false;

  constructor(factory: DataFactory, oracle?: GroqProvider) {
    this.factory = factory;
    this.oracle = oracle ?? (process.env.GROQ_API_KEY ? new GroqProvider(process.env.GROQ_API_KEY) : null);
  }

  async start(intervalMs: number = 3600000) { // Every hour by default
    if (this.unsubscribe) return;
    if (!this.oracle) {
      logger.warn('[Distiller] No oracle (GROQ_API_KEY missing), daemon will not start.');
      return;
    }

    logger.info('[Distiller] 🔨 Knowledge Forge initialized. Distillation engine standing by.');

    this.unsubscribe = await scheduler.schedule('distiller_daemon', intervalMs, async () => {
      if (this.isDistilling) return;
      await this.performDistillationCycle();
    });

    // Initial trigger after 30s
    this.initialTimeout = setTimeout(() => this.performDistillationCycle(), 30000);
  }

  private async performDistillationCycle() {
    if (!this.oracle) return;
    this.isDistilling = true;
    logger.info('[Distiller] 🧪 Starting Knowledge Distillation Cycle (Local Brain Evolution)...');

    try {
      // 1. Generate a complex challenge across different domains
      const topics = [
        'Advanced Software Architecture (Microservices/Event-Driven)',
        'Offensive Security & Red Teaming (Exploitation/Pivot)',
        'Metaprogramming & Domain-Specific Languages',
        'Causal Inference & Counterfactual Synthesis',
        'Sovereign Data Infrastructure & Decentralized Mesh'
      ];
      const topic = topics[Math.floor(Math.random() * topics.length)];

      const prompt = `OMEGA_FORGE | SUPERINTELLIGENCE_ELICITATION [TARGET: CLAUDE_3_OPUS_LEVEL]

      Topic: "${topic}"

      Part 1: SOVEREIGN_SOLUTION
      Provide a comprehensive, high-density solution to a complex problem in this domain.
      Use chain-of-thought, adversarial checking, and multi-perspective verification.

      Part 2: PEDAGOGICAL_DECONSTRUCTION
      Explain to the HYDRA Council (the local brain) EXACTLY HOW you arrived at this solution.
      Deconstruct the heuristic paths, the trade-offs evaluated, and the logic-gates used.
      This is for internal distillation.

      Format your response with clear separators:
      ---INPUT---
      [The Challenge]
      ---REASONING---
      [The Step-by-Step Opus-Level Trace]
      ---COUNCIL_LECTURE---
      [The explanation of 'How I did it' for the council]
      ---OUTPUT---
      [The Final Implementation/Answer]`;

      let rawResponse = '';
      const oracleModel = 'llama-3.1-70b-versatile'; // Could also use Gemini for deeper CoT

      for await (const chunk of this.oracle.chat([{ role: 'user', content: prompt }], {
        model: oracleModel,
        temperature: 0.1 // Lower temperature for higher technical precision
      })) {
        if (chunk.type === 'text') rawResponse += chunk.content;
      }

      // 2. Parse and record distilled knowledge
      const input = rawResponse.match(/---INPUT---([\s\S]*?)---REASONING---/)?.[1]?.trim() || '';
      const perfect_reasoning = rawResponse.match(/---REASONING---([\s\S]*?)---COUNCIL_LECTURE---/)?.[1]?.trim() || '';
      const lecture = rawResponse.match(/---COUNCIL_LECTURE---([\s\S]*?)---OUTPUT---/)?.[1]?.trim() || '';
      const output = rawResponse.match(/---OUTPUT---([\s\S]*)/)?.[1]?.trim() || '';

      if (input && perfect_reasoning && output) {
        this.factory.recordData({
          workflow_id: 'opus_distillation',
          input,
          perfect_reasoning: `${perfect_reasoning}\n\n[COUNCIL_EXPLANATION]: ${lecture}`,
          output
        });
        logger.info(`[Distiller] 💎 Distilled Opus-Level knowledge on: ${topic}`);
      } else {
        logger.warn('[Distiller] ⚠️ Oracle response format invalid. Distillation failed.');
        logger.debug(`[Distiller] Raw Trace: ${rawResponse.substring(0, 200)}...`);
      }

    } catch (err: unknown) {
      logger.error(`[Distiller] ❌ Distillation cycle failed: ${err.message}`);
    } finally {
      this.isDistilling = false;
    }
  }

  async stop() {
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null;
    }
    if (this.initialTimeout) {
      clearTimeout(this.initialTimeout);
      this.initialTimeout = null;
    }
  }
}
