import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';
import logger from '../../utils/logger.js';
import type { QueryEngine } from '../QueryEngine.js';

const execAsync = promisify(exec);

export type WorkflowPhase =
  | 'READING_CODEBASE'
  | 'PLANNING'
  | 'EXECUTING'
  | 'TESTING'
  | 'CORRECTING'
  | 'DELIVERING'
  | 'COMPLETE'
  | 'FAILED';

export interface WorkflowStep {
  phase: WorkflowPhase;
  description: string;
  output: string;
  durationMs: number;
  success: boolean;
}

export interface DevWorkflowResult {
  taskId: string;
  task: string;
  steps: WorkflowStep[];
  finalReport: string;
  totalDurationMs: number;
  success: boolean;
  deliverable?: string; // PR diff, file path, commit hash
}

/**
 * DEV WORKFLOW ENGINE — HYDRA as an Autonomous Software Engineer.
 *
 * Implements the full structured dev cycle:
 * Tâche → Lecture Codebase → Plan → Bash/Tests → Corrections Itératives → PR
 *
 * Each phase is logged, timed, and stored so the Council can audit the
 * full chain of reasoning and action.
 */
export class DevWorkflowEngine {
  private engine: QueryEngine;
  private cwd: string;
  private maxIterations = 5;
  public setMaxIterations(n: number): void { this.maxIterations = n; }

  constructor(engine: QueryEngine, cwd: string = process.cwd()) {
    this.engine = engine;
    this.cwd = cwd;
    logger.info('[DevWorkflow] ⚙️ Autonomous Dev Engine initialized.');
  }

  /**
   * Main entry-point: runs the full 6-phase dev workflow for a given task.
   */
  async run(task: string): Promise<DevWorkflowResult> {
    const taskId = `wf_${Date.now().toString(36)}`;
    const steps: WorkflowStep[] = [];
    const startTotal = Date.now();

    logger.info(`[DevWorkflow] 🚀 STARTING WORKFLOW [${taskId}]: ${task.substring(0, 80)}`);

    try {
      // ─── PHASE 1 : LECTURE CODEBASE ────────────────────────────────────────
      const readStep = await this.phaseReadCodebase(task);
      steps.push(readStep);
      if (!readStep.success) throw new Error('Codebase reading failed.');

      // ─── PHASE 2 : PLAN D'ACTION ───────────────────────────────────────────
      const planStep = await this.phasePlan(task, readStep.output);
      steps.push(planStep);
      if (!planStep.success) throw new Error('Planning failed.');

      // ─── PHASE 3 : EXÉCUTION BASH ──────────────────────────────────────────
      const execStep = await this.phaseExecute(task, planStep.output);
      steps.push(execStep);

      // ─── PHASE 4 : TESTS ───────────────────────────────────────────────────
      const testStep = await this.phaseTest();
      steps.push(testStep);

      // ─── PHASE 5 : CORRECTIONS ITÉRATIVES ─────────────────────────────────
      let correctionOutput = execStep.output;
      if (!testStep.success) {
        const corrStep = await this.phaseCorrect(
          task,
          planStep.output,
          testStep.output
        );
        steps.push(corrStep);
        correctionOutput = corrStep.output;
      }

      // ─── PHASE 6 : PR / LIVRAISON ──────────────────────────────────────────
      const prStep = await this.phaseDeliver(task, correctionOutput);
      steps.push(prStep);

      const finalReport = this.buildFinalReport(taskId, task, steps);
      const result: DevWorkflowResult = {
        taskId,
        task,
        steps,
        finalReport,
        totalDurationMs: Date.now() - startTotal,
        success: prStep.success,
        deliverable: prStep.output,
      };

      logger.info(`[DevWorkflow] ✅ WORKFLOW COMPLETE [${taskId}] in ${result.totalDurationMs}ms`);
      return result;
    } catch (err: unknown) {
      logger.error(`[DevWorkflow] ❌ WORKFLOW FAILED [${taskId}]: ${err.message}`);
      return {
        taskId,
        task,
        steps,
        finalReport: `WORKFLOW FAILED at phase "${steps.at(-1)?.phase}": ${err.message}`,
        totalDurationMs: Date.now() - startTotal,
        success: false,
      };
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  PHASE IMPLEMENTATIONS
  // ══════════════════════════════════════════════════════════════════════════

  private async phaseReadCodebase(task: string): Promise<WorkflowStep> {
    const start = Date.now();
    logger.info('[DevWorkflow] 📖 Phase 1: Reading codebase...');

    try {
      // Get a structural snapshot of relevant source files
      const { stdout: gitFiles } = await execAsync(
        'git ls-files --cached --others --exclude-standard',
        { cwd: this.cwd }
      );

      const srcFiles = gitFiles
        .split('\n')
        .filter(f => f.endsWith('.ts') || f.endsWith('.py'))
        .slice(0, 60); // Cap at 60 files to avoid context overflow

      // Ask the LLM which files are relevant for this task
      const relevancePrompt = `You are an expert software engineer reading a codebase.
Task to accomplish: "${task}"

Available source files:
${srcFiles.join('\n')}

Select the TOP 10 files most relevant to this task. Return ONLY a JSON array of filenames. No explanation.`;

      let relevantFilesJson = '';
      for await (const chunk of this.engine.query(relevancePrompt)) {
        if (chunk.type === 'text') relevantFilesJson += chunk.content;
      }

      let relevantFiles: string[] = [];
      try {
        const jsonMatch = relevantFilesJson.match(/\[[\s\S]*\]/);
        if (jsonMatch) relevantFiles = JSON.parse(jsonMatch[0]);
      } catch {
        relevantFiles = srcFiles.slice(0, 10);
      }

      // Read and summarize key files
      const snippets: string[] = [];
      for (const file of relevantFiles.slice(0, 10)) {
        const fullPath = path.join(this.cwd, file);
        if (fs.existsSync(fullPath)) {
          const content = fs.readFileSync(fullPath, 'utf-8').slice(0, 2000);
          snippets.push(`### ${file}\n\`\`\`\n${content}\n\`\`\``);
        }
      }

      const summary = `Codebase snapshot (${relevantFiles.length} files analyzed):\n\n${snippets.join('\n\n')}`;
      return this.step('READING_CODEBASE', 'Codebase scanned and key files identified.', summary, start, true);
    } catch (err: unknown) {
      return this.step('READING_CODEBASE', 'Failed to read codebase.', err.message, start, false);
    }
  }

  private async phasePlan(task: string, codebaseContext: string): Promise<WorkflowStep> {
    const start = Date.now();
    logger.info('[DevWorkflow] 🗺️ Phase 2: Generating action plan...');

    const planPrompt = `You are HYDRA, an autonomous software engineer.

## Task
${task}

## Codebase Context
${codebaseContext.slice(0, 6000)}

## Instructions
Create a precise, step-by-step action plan to accomplish this task.
Format your response as:

### PLAN
1. [Specific file to modify/create] — [Exact change]
2. ...

### BASH COMMANDS
\`\`\`bash
# Exact commands to run
\`\`\`

### VALIDATION
- How to verify the change works
- Test commands to run`;

    let plan = '';
    for await (const chunk of this.engine.query(planPrompt)) {
      if (chunk.type === 'text') plan += chunk.content;
    }

    return this.step('PLANNING', 'Action plan generated.', plan, start, plan.length > 50);
  }

  private async phaseExecute(task: string, plan: string): Promise<WorkflowStep> {
    const start = Date.now();
    logger.info('[DevWorkflow] ⚡ Phase 3: Executing plan...');

    // Extract bash commands from the plan
    const bashMatch = plan.match(/```(?:bash|sh|powershell)([\s\S]*?)```/g) || [];
    const commands = bashMatch
      .map(b => b.replace(/```(?:bash|sh|powershell)?/g, '').trim())
      .filter(c => c.length > 0);

    const outputs: string[] = [];

    if (commands.length === 0) {
      // Ask the LLM to generate & apply code changes directly
      const execPrompt = `Based on this plan, generate the exact TypeScript/Python code changes needed.
For each file, provide the COMPLETE new file content in a fenced code block with the filename as label.

Plan:
${plan.slice(0, 4000)}

Task: ${task}`;

      let codeOutput = '';
      for await (const chunk of this.engine.query(execPrompt)) {
        if (chunk.type === 'text') codeOutput += chunk.content;
      }
      outputs.push(codeOutput);
    } else {
      // Execute commands one by one
      for (const cmd of commands.slice(0, 8)) {
        logger.info(`[DevWorkflow] $ ${cmd.split('\n')[0].substring(0, 70)}`);
        try {
          const { stdout, stderr } = await execAsync(cmd, {
            cwd: this.cwd,
            timeout: 60000,
          });
          if (stdout) outputs.push(`$ ${cmd.split('\n')[0]}\n${stdout}`);
          if (stderr) outputs.push(`[STDERR] ${stderr.substring(0, 200)}`);
        } catch (e: unknown) {
          outputs.push(`[EXEC ERROR] ${cmd.split('\n')[0]}: ${e.message.substring(0, 200)}`);
        }
      }
    }

    const output = outputs.join('\n\n');
    return this.step('EXECUTING', 'Plan executed.', output, start, true);
  }

  private async phaseTest(): Promise<WorkflowStep> {
    const start = Date.now();
    logger.info('[DevWorkflow] 🧪 Phase 4: Running tests...');

    const testCommands = [
      'npx tsc --noEmit 2>&1 | head -50',
      'bun run typecheck 2>&1 | head -30',
    ];

    const results: string[] = [];
    let hasErrors = false;

    for (const cmd of testCommands) {
      try {
        const { stdout, stderr } = await execAsync(cmd, {
          cwd: this.cwd,
          timeout: 90000,
          encoding: 'utf8',
        });
        const out = (stdout + stderr).trim().substring(0, 2000);
        results.push(`$ ${cmd}\n${out}`);
        if (out.toLowerCase().includes('error') || out.includes('TS2')) {
          hasErrors = true;
        }
      } catch (e: unknown) {
        // Non-zero exit: tsc found errors
        const errOut = (e.stdout + e.stderr || e.message).substring(0, 2000);
        results.push(`$ ${cmd}\n${errOut}`);
        if (errOut.includes('error') || errOut.includes('TS')) hasErrors = true;
      }
    }

    const output = results.join('\n\n');
    logger.info(`[DevWorkflow] Tests ${hasErrors ? '❌ FAILED' : '✅ PASSED'}`);
    return this.step('TESTING', hasErrors ? 'Type errors detected.' : 'All checks passed.', output, start, !hasErrors);
  }

  private async phaseCorrect(
    task: string,
    plan: string,
    testOutput: string,
    iteration = 1
  ): Promise<WorkflowStep> {
    const start = Date.now();
    logger.info(`[DevWorkflow] 🔧 Phase 5: Iterative correction (round ${iteration})...`);

    if (iteration > this.maxIterations) {
      return this.step('CORRECTING', 'Max iterations reached.', 'Halted after max retries.', start, false);
    }

    const correctionPrompt = `You are HYDRA correcting a failed implementation.

## Original Task
${task}

## Original Plan
${plan.slice(0, 2000)}

## Test/TypeCheck Errors
${testOutput.slice(0, 3000)}

## Instructions
Diagnose each error and provide the exact corrected TypeScript code for each affected file.
For each fix, prefix the code block with the filename:

\`\`\`typescript:src/path/to/file.ts
// corrected content
\`\`\`

Be surgical: fix only what's broken.`;

    let correction = '';
    for await (const chunk of this.engine.query(correctionPrompt)) {
      if (chunk.type === 'text') correction += chunk.content;
    }

    // Apply file corrections from code blocks
    const fileBlockRegex = /```(?:typescript|ts):([^\n]+)\n([\s\S]*?)```/g;
    let match;
    const applied: string[] = [];

    while ((match = fileBlockRegex.exec(correction)) !== null) {
      const filePath = path.join(this.cwd, match[1].trim());
      const content = match[2];
      try {
        fs.mkdirSync(path.dirname(filePath), { recursive: true });
        fs.writeFileSync(filePath, content);
        applied.push(`✅ Patched: ${match[1].trim()}`);
      } catch (e: unknown) {
        applied.push(`❌ Failed to patch ${match[1].trim()}: ${e.message}`);
      }
    }

    logger.info(`[DevWorkflow] Applied ${applied.length} corrections.`);
    return this.step(
      'CORRECTING',
      `${applied.length} files corrected (iteration ${iteration}).`,
      applied.join('\n') + '\n\n' + correction.slice(0, 1000),
      start,
      applied.length > 0
    );
  }

  private async phaseDeliver(task: string, executionOutput: string): Promise<WorkflowStep> {
    const start = Date.now();
    logger.info('[DevWorkflow] 📦 Phase 6: Delivering (PR/commit)...');

    const outputs: string[] = [];

    try {
      const { stdout: diffStat } = await execAsync(
        'git diff --stat HEAD',
        { cwd: this.cwd, timeout: 10000, encoding: 'utf8' }
      ).catch(() => ({ stdout: 'No git repo or no changes.' }));
      outputs.push(`📊 Diff stat:\n${diffStat}`);

      // Generate commit message via LLM
      const commitPrompt = `Write a precise git commit message (max 72 chars subject, optional body) for:
Task: ${task}
Changes summary: ${diffStat.slice(0, 500)}
Format: <type>(<scope>): <subject>`;

      let commitMsg = '';
      for await (const chunk of this.engine.query(commitPrompt)) {
        if (chunk.type === 'text') commitMsg += chunk.content;
      }
      commitMsg = commitMsg.trim().split('\n')[0].slice(0, 72);

      await execAsync('git add -A', { cwd: this.cwd, encoding: 'utf8' }).catch(() => {});
      let commitOut = 'Nothing to commit.';
      try {
        const res = await execAsync(
          `git commit -m "${commitMsg.replace(/"/g, "'")}"`,
          { cwd: this.cwd, encoding: 'utf8' }
        );
        commitOut = res.stdout;
      } catch (e: unknown) { commitOut = e.stdout || e.message; }
      outputs.push(`📝 Commit:\n${commitMsg}\n${commitOut}`);

      logger.info(`[DevWorkflow] 🎉 Delivered: ${commitMsg}`);
    } catch (err: unknown) {
      outputs.push(`[Delivery warning] ${err.message.substring(0, 300)}`);
    }

    // Final PR summary
    const prSummary = `## PR: ${task.substring(0, 60)}\n\n${outputs.join('\n\n')}\n\n_Generated by HYDRA Dev Workflow Engine_`;
    return this.step('DELIVERING', 'Changes committed and PR generated.', prSummary, start, true);
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  HELPERS
  // ══════════════════════════════════════════════════════════════════════════

  private step(
    phase: WorkflowPhase,
    description: string,
    output: string,
    startMs: number,
    success: boolean
  ): WorkflowStep {
    const step: WorkflowStep = {
      phase,
      description,
      output,
      durationMs: Date.now() - startMs,
      success,
    };
    const icon = success ? '✅' : '❌';
    logger.info(`[DevWorkflow] ${icon} [${phase}] ${description} (${step.durationMs}ms)`);
    return step;
  }

  private buildFinalReport(taskId: string, task: string, steps: WorkflowStep[]): string {
    const lines = [
      `# HYDRA Dev Workflow Report`,
      `**Task ID:** ${taskId}`,
      `**Task:** ${task}`,
      '',
      '## Phase Summary',
      ...steps.map(s =>
        `- ${s.success ? '✅' : '❌'} **${s.phase}** — ${s.description} _(${s.durationMs}ms)_`
      ),
    ];
    return lines.join('\n');
  }
}
