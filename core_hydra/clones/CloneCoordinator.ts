import { randomUUID } from 'crypto';
import type { QueryEngine } from '../QueryEngine.js';
import type { ToolContext } from '../../tools/Tool.js';
import { CloneClass, type CloneMetadata } from './CloneTypes.js';
import { SpiderWeb, type ISpiderNode } from './SpiderWeb.js';
import { LegionEngine } from './LegionEngine.js';
import logger from '../../utils/logger.js';
import { EventEmitter } from 'events';
import { Genome } from '../../evolution/Genome.js';
import { ArcheDeNoe } from '../../evolution/ArcheDeNoe.js';
import { scheduler } from '../../polyglot/scheduler.js';
import { CRISPR_Titan, type MutationStrategy } from '../../evolution/CRISPR_Titan.js';
import { ChromosomeType } from '../../evolution/UnifiedGenome.js';
import { TitanRL, type TaskResult } from '../../evolution/TitanRL.js';
import { KarmicMemory } from '../../evolution/KarmicMemory.js';
import { DreamWeaver } from '../../evolution/DreamWeaver.js';
import { GlobalTitanNVM } from '../../nvm/TitanNVM.js';
import { HydraCore } from '../hydra/HydraCore.js';
import { PANTHEON } from '../hydra/Pantheon.js';
import { errorMessage } from '../../types/index.js';

export interface SubClone {
  metadata: CloneMetadata;
  engine: QueryEngine;
  genome: Genome; // INTÉGRATION TITAN-EVO
  result?: string;
  assignedSpiderNodeId?: string;
  resourceAllocation: {
    cpuShare: number;
    gpuShare: number;
    memoryMB: number;
    priority: number;
  };
  lastActivity: number;
  hierarchyLevel: number;
  parentCloneId?: string;
  voteWeight: number;
}

export interface CloneTask {
  id: string;
  cloneId?: string;
  type: 'inference' | 'analysis' | 'research' | 'coding' | 'spider_harvest' | 'multi_stage' | 'consensus_vote' | 'orchestrator_directive';
  payload: unknown;
  priority: number;
  requiresSpiderPower: boolean;
  requiresConsensus?: boolean;
}

export interface ConsensusVote {
  cloneId: string;
  vote: 'yes' | 'no' | 'abstain';
  weight: number;
  reason: string;
  timestamp: number;
}

export interface RealTimeDashboard {
  timestamp: number;
  totalClones: number;
  activeClones: number;
  harvestedPower: number;
  hierarchyDepth: number;
  activeParallelGroups: number;
  pendingTasks: number;
  topContributors: Array<{ cloneId: string; power: number }>;
}

/**
 * AGENT ORCHESTRATOR v4.0
 * Manages hierarchical agent intelligence, distributed compute allocation, and task queuing.
 */
export class CloneCoordinator extends EventEmitter {
  private clones: Map<string, SubClone> = new Map();
  private context: ToolContext;
  private parentEngine: QueryEngine;
  private spiderWeb: SpiderWeb;
  private pendingTasksQueue: CloneTask[] = [];
  private activeTasksCount = 0;
  private maxConcurrentTasks = 5;
  private maxHierarchyDepth = 5;
  private lastScalingAction = Date.now();

  // TITAN-EVO MODULES
  private arche: ArcheDeNoe;
  private crispr: CRISPR_Titan;
  private titanRL: TitanRL;

  // TITAN-LEGION
  public legionEngine!: LegionEngine;

  // CLUSTER 3 : RÊVES & MÉMOIRE
  private karmicMemory: KarmicMemory;
  private dreamWeaver: DreamWeaver;

  // ARCHITECTURE HYDRA
  public hydra: HydraCore;

  private scalingPolicy = {
    minClones: 5,
    maxClones: 30,
    scaleUpThreshold: 0.8,
    scaleDownThreshold: 0.25,
    coolDownMs: 15000
  };

  constructor(parentEngine: QueryEngine) {
    super();
    this.parentEngine = parentEngine;
    // Minimal ToolContext for sub-agents. Real permission checks happen in main.tsx
    // when these tools are called through the parent engine.
    this.context = {
      cwd: process.cwd(),
      permissions: {
        check: () => 'ALLOW',
      } as unknown as ToolContext['permissions'],
    };
    this.spiderWeb = new SpiderWeb();

    // Init TITAN-EVO
    this.arche = new ArcheDeNoe(5000);
    this.crispr = new CRISPR_Titan(this.arche);
    this.titanRL = new TitanRL();

    // Init Rêves & Mémoire (Cluster 3)
    this.karmicMemory = new KarmicMemory();
    this.dreamWeaver = new DreamWeaver(this, this.karmicMemory);

    // Initialisation de l'écosystème et de la Légion
    const { TitanEcosystem } = require('../../evolution/TitanEcosystem.js');
    const ecosystem = new TitanEcosystem();
    this.legionEngine = new LegionEngine(ecosystem);

    // Init Architecture HYDRA
    this.hydra = new HydraCore();

    // Auto-management loops (via polyglot scheduler, TS fallback if Go unavailable)
    scheduler.schedule('clone_auto_scale', 10_000, () => this.autoScaleAndRebalance())
      .catch((e) => {
        logger.warn(`[CloneCoordinator] scheduler.schedule failed for auto_scale, using setInterval: ${e instanceof Error ? e.message : e}`);
        setInterval(() => this.autoScaleAndRebalance(), 10_000);
      });
    scheduler.schedule('clone_process_pending', 1_000, () => this.processPendingTasks())
      .catch((e) => {
        logger.warn(`[CloneCoordinator] scheduler.schedule failed for process_pending, using setInterval: ${e instanceof Error ? e.message : e}`);
        setInterval(() => this.processPendingTasks(), 1_000);
      });

    // Initialiser les 10 Dieux
    setTimeout(() => this.initializeOlympus(), 2000);
  }

  /**
   * Instancie les 10 Agents Olympiens définis dans le Panthéon
   */
  private async initializeOlympus() {
    logger.info('[HYDRA] 🏛️ Invocation des 10 Agents Olympiens...');
    for (const config of Object.values(PANTHEON)) {
      await this.createClone(
        config.name,
        config.specialty,
        CloneClass.HIERARCHICAL,
        undefined,
        config.id === 'zeus' ? 0 : 1
      );
    }
  }

  public async spawnClone(
    mission: string,
    cloneClass: CloneClass = CloneClass.PRECISE,
    parentCloneId?: string,
    requiresSpiderPower: boolean = false
  ): Promise<string> {
    const parentSovereign = parentCloneId ? this.clones.get(parentCloneId)?.metadata.sovereignParent || 'ZEUS' : 'ZEUS';
    
    // Délégation au LegionEngine
    const cloneMeta = await this.legionEngine.spawnBySovereign(parentSovereign, cloneClass, mission);
    if (!cloneMeta) {
      throw new Error(`[CloneCoordinator] LegionEngine a refusé ou mis en attente le clone pour la mission: ${mission}`);
    }

    const newEngine = this.parentEngine.clone(cloneMeta.id);

    // Initialisation du génome avec TITAN-EVO (via l'écosystème ou nouveau)
    const childGenome = new Genome(cloneMeta.name);

    const allocation = this.calculateDynamicAllocation(cloneClass, 5);

    const newClone: SubClone = {
      metadata: cloneMeta,
      engine: newEngine,
      genome: childGenome,
      resourceAllocation: allocation,
      lastActivity: Date.now(),
      hierarchyLevel: parentCloneId ? (this.clones.get(parentCloneId)?.hierarchyLevel || 0) + 1 : 0,
      parentCloneId,
      voteWeight: cloneClass === CloneClass.ORCHESTRATOR ? 2.0 : 1.0,
    };

    // On synchronise la metadata du LegionEngine
    newClone.metadata = cloneMeta;

    this.clones.set(cloneMeta.id, newClone);
    logger.info(`[CloneCoordinator] 🌱 New clone spawned via LegionEngine: ${cloneMeta.id} (Class: ${cloneClass}) for mission: ${mission}`);

    // Log the genesis in Karmic Memory
    this.karmicMemory.recordBirth(cloneMeta.id, childGenome);

    this.autoScaleAndRebalance();
    return cloneMeta.id;
  }

  async createClone(
    name: string,
    purpose: string,
    type: CloneClass = CloneClass.FREE,
    parentCloneId?: string,
    hierarchyLevel = 0,
    passedGenome?: Genome
  ): Promise<string> {
    if (hierarchyLevel > this.maxHierarchyDepth) {
      logger.warn(`[Agent Orchestrator] Max depth reached for ${name}. Refusing creation.`);
      return '';
    }

    const id = `cln_${randomUUID().split('-')[0]}`;
    const { QueryEngine } = await import('../QueryEngine.js');

    let tools = this.getFilteredTools(type);
    
    // Assign or create Genome
    const genome = passedGenome || new Genome(name);
    
    const finalPurpose = `${purpose} | Traits: ${genome.specialties.join(', ')}. Bias: ${genome.params.promptMutation}`;
    const systemPrompt = CloneCoordinator.buildSystemPrompt(name, finalPurpose, type, hierarchyLevel);
    
    const priority = type === CloneClass.PRECISE ? 9 : 5;
    const temperature = genome.params.temperature;

    const engineClone = new QueryEngine({
      provider: this.parentEngine.getProvider(),
      model: this.parentEngine.getModel(),
      temperature,
      systemPrompt,
      tools,
    });

    if (type === CloneClass.HIERARCHICAL) {
      await this.injectAgentTool(engineClone);
    }

    const allocation = this.calculateDynamicAllocation(type, priority);

    const cloneObj: SubClone = {
      metadata: {
        id,
        name,
        purpose,
        status: 'idle',
        cloneClass: type,
        createdAt: Date.now(),
        agentConfigurationId: genome.id,
        specialties: genome.specialties.join(', ')
      },
      engine: engineClone,
      genome: genome,
      resourceAllocation: allocation,
      lastActivity: Date.now(),
      hierarchyLevel,
      parentCloneId,
      voteWeight: 1.0 / (hierarchyLevel + 1)
    };

    this.clones.set(id, cloneObj);
    logger.info(`[Agent Orchestrator] 🤖 Spawned Lvl ${hierarchyLevel} Evolutive Agent: ${name} (Gen: ${genome.generation})`);
    
    // Log Titan-NVM status
    if (GlobalTitanNVM.isNativeEngine()) {
      logger.debug(`[TITAN-NVM] Native memory allocation verified for Agent ${name}.`);
    } else {
      logger.debug(`[TITAN-NVM] Using JS simulated memory for Agent ${name}.`);
    }

    this.emit('clone:created', cloneObj.metadata);
    return id;
  }

  public listSubClones(): SubClone[] {
    return Array.from(this.clones.values());
  }

  public promoteToLeader(id: string, domain: string) {
    const clone = this.clones.get(id);
    if (clone) {
      clone.metadata.cloneClass = CloneClass.ORCHESTRATOR;
      clone.metadata.name = `ORCHESTRATOR_${clone.metadata.name}`;
      clone.metadata.purpose = `Manage Domain: ${domain}. Assure robust task delegation and recruit workers.`;
      
      clone.engine.setSystemPrompt(CloneCoordinator.buildSystemPrompt(clone.metadata.name, clone.metadata.purpose, clone.metadata.cloneClass, clone.hierarchyLevel));
      
      logger.info(`[Agent Orchestrator] 👑 Agent ${id} PROMOTED to ORCHESTRATOR in domain ${domain}`);
    }
  }

  // ====================== CONSENSUS VOTING ======================

  async runConsensusVote(question: string, threshold = 0.6): Promise<boolean> {
    logger.info(`[Agent Orchestrator] 🗳️ Initiating Consensus Vote: "${question}"`);
    const votes: ConsensusVote[] = [];
    const voters = Array.from(this.clones.values()).filter(c => c.metadata.status !== 'paused');

    const voteTasks = voters.map(async (clone) => {
      let voteText = '';
      try {
        for await (const chunk of clone.engine.query(`VOTE REQUIRED: Execute "${question}"? Reply YES, NO or ABSTAIN.`)) {
          if (chunk.type === 'text') voteText += chunk.content;
        }
      } catch (err) {
        voteText = 'ABSTAIN';
      }
      
      const decision = voteText.toUpperCase().includes('YES') ? 'yes' : (voteText.toUpperCase().includes('NO') ? 'no' : 'abstain');
      votes.push({
        cloneId: clone.metadata.id,
        vote: decision as 'yes' | 'no' | 'abstain',
        weight: clone.voteWeight,
        reason: voteText,
        timestamp: Date.now()
      });
    });

    await Promise.allSettled(voteTasks);
    const totalWeight = votes.reduce((acc, v) => acc + v.weight, 0);
    const yesWeight = votes.filter(v => v.vote === 'yes').reduce((acc, v) => acc + v.weight, 0);
    const result = totalWeight > 0 ? (yesWeight / totalWeight) >= threshold : false;

    logger.info(`[Agent Orchestrator] Consensus Result: ${result ? '✅ APPROVED' : '❌ REJECTED'} (${totalWeight > 0 ? (yesWeight / totalWeight * 100).toFixed(1) : 0}% weight)`);
    return result;
  }

  // ====================== RESOURCE MANAGEMENT ======================

  private autoScaleAndRebalance() {
    const now = Date.now();
    if (now - this.lastScalingAction < this.scalingPolicy.coolDownMs) return;
    const metrics = this.getRealTimeDashboard();
    const activeRatio = metrics.totalClones > 0 ? metrics.activeClones / metrics.totalClones : 0;

    if (activeRatio > this.scalingPolicy.scaleUpThreshold && metrics.totalClones < this.scalingPolicy.maxClones) {
      this.createClone(`Worker-${now.toString(36)}`, 'Load-balancing reinforcement', CloneClass.FREE);
      this.lastScalingAction = now;
    } else if (activeRatio < this.scalingPolicy.scaleDownThreshold && metrics.totalClones > this.scalingPolicy.minClones) {
      const oldest = Array.from(this.clones.values()).sort((a, b) => a.lastActivity - b.lastActivity)[0];
      if (oldest && oldest.metadata.status === 'idle') {
        this.killClone(oldest.metadata.id);
        this.lastScalingAction = now;
      }
    }
  }

  private calculateDynamicAllocation(type: CloneClass, priority: number) {
    const harvested = this.getSpiderHarvestedPower();
    return {
      cpuShare: Math.min(1.0, 0.2 + (priority * 0.08)),
      gpuShare: Math.min(0.9, (type === CloneClass.PRECISE ? 0.4 : 0.2) * harvested),
      memoryMB: type === CloneClass.PRECISE ? 2048 : 1024,
      priority
    };
  }

  /**
   * Pure function: compute resource allocation for a clone.
   * Exposed static for unit testing.
   */
  public static computeResourceAllocation(
    cloneClass: CloneClass,
    priority: number,
    harvestedPower: number = 1.0
  ): { cpuShare: number; gpuShare: number; memoryMB: number; priority: number } {
    return {
      cpuShare: Math.min(1.0, 0.2 + (priority * 0.08)),
      gpuShare: Math.min(0.9, (cloneClass === CloneClass.PRECISE ? 0.4 : 0.2) * harvestedPower),
      memoryMB: cloneClass === CloneClass.PRECISE ? 2048 : 1024,
      priority,
    };
  }

  private getFilteredTools(type: CloneClass) {
    const parentTools = this.parentEngine.getAllTools();
    if (type === CloneClass.PRECISE) {
      return parentTools.filter((t) => t.name.startsWith('file_') || t.name.includes('read'));
    }
    return parentTools;
  }

  /**
   * Pure function: build the system prompt for a clone.
   * Exposed static for unit testing without coordinator instantiation.
   */
  public static buildSystemPrompt(name: string, purpose: string, type: CloneClass, level: number): string {
    if (type === CloneClass.ORCHESTRATOR) {
      return `You are "${name}" (Lvl ${level}), an ORCHESTRATOR AGENT.
              Class: ORCHESTRATOR.
              Objective: ${purpose}

              You command sub-agents and can requisition workers to fulfill complex task pipelines.
              WORKFLOW: Plan -> Delegate -> Execute -> Verify.
              Ensure efficient resource usage.`;
    }

    return `You are AGENT "${name}" (Lvl ${level}). Class: ${type}.
            Objective: ${purpose}.
            Status: ${type === CloneClass.FREE ? 'Autonomous Worker' : 'Specialized Asset'}.

            WORKFLOW: Input -> Analyze -> Tool Calls -> Structured Response.
            Always act professionally and logically. Return accurate reports.`;
  }

  private async injectAgentTool(engine: QueryEngine) {
    const { AgentTool } = await import('../../tools/agents/AgentTool.js');
    const subCoordinator = new CloneCoordinator(engine);
    const agentTool = new AgentTool(subCoordinator);
    engine.registerTool({
      name: agentTool.name,
      description: agentTool.description,
      parameters: agentTool.parameters,
      execute: async (args: Record<string, unknown>) => {
        const cloneClassRaw = String(args.cloneClass ?? 'PRECISE');
        const validClass = (Object.values(CloneClass) as string[]).includes(cloneClassRaw)
          ? (cloneClassRaw as CloneClass)
          : CloneClass.PRECISE;
        return agentTool.execute(
          {
            name: String(args.name ?? 'sub-agent'),
            purpose: String(args.purpose ?? ''),
            task: String(args.task ?? ''),
            cloneClass: validClass,
          },
          this.context,
        );
      },
    });
  }

  // ====================== TASK EXECUTION ======================
  
  public enqueueTask(task: CloneTask) {
    if (this.dreamWeaver) this.dreamWeaver.wakeUp();
    this.pendingTasksQueue.push(task);
    this.pendingTasksQueue.sort((a, b) => b.priority - a.priority); // Highest priority first
  }

  async runCloneTask(id: string, task: string | Record<string, unknown>, opts: Partial<CloneTask> = {}): Promise<string> {
    if (this.dreamWeaver) this.dreamWeaver.wakeUp();
    const clone = this.clones.get(id);
    if (!clone) throw new Error(`Agent ${id} not found`);
    if (clone.metadata.status === 'paused') return `Agent ${id} is PAUSED.`;

    const taskString = typeof task === 'string' ? task : JSON.stringify(task);

    if (opts.requiresConsensus) {
      const approved = await this.runConsensusVote(`Execute high-risk task: ${taskString.substring(0, 50)}?`);
      if (!approved) return "TASK ABORTED: Consensus not reached.";
    }

    clone.metadata.status = 'working';
    clone.lastActivity = Date.now();
    let result = '';
    const startTime = Date.now();
    let success = true;

    try {
      for await (const chunk of clone.engine.query(taskString)) {
        if (chunk.type === 'text') result += chunk.content;
      }
    } catch (err) {
      success = false;
      result = `ERROR: ${errorMessage(err)}`;
    }

    // TITAN-EVO: RL Execution & Evolution trigger
    const durationSec = (Date.now() - startTime) / 1000;
    const taskResult: TaskResult = {
      success,
      efficiency: success ? 0.9 : 0.2, // Mocked for integration
      novelty: Math.random(), // Simulating novelty detection
      error_rate: success ? 0 : 1,
      ram_used: clone.resourceAllocation.memoryMB,
      time: durationSec,
      user_interventions: 0,
      helped_agents: 0,
      states_explored: Math.floor(Math.random() * 20),
      safe: true,
      user_satisfaction: success ? 0.8 : 0.1
    };

    const fitness = await this.titanRL.learn(clone.genome, taskResult);
    logger.debug(`[TITAN-EVO] Agent ${clone.metadata.name} achieved fitness: ${fitness.toFixed(2)}`);

    // Evolution Check
    if (clone.genome.fitnessHistory.length > 0 && clone.genome.fitnessHistory.length % 5 === 0) {
      logger.info(`[TITAN-EVO] 🧬 Agent ${clone.metadata.name} triggers Evolution Cycle.`);
      this.arche.store(clone.genome);
      clone.genome.generation += 1;
      
      if (fitness < 0.4) {
        // Punish and mutate
        logger.warn(`[TITAN-EVO] Low fitness (${fitness.toFixed(2)}). Triggering CRISPR mutation.`);
        this.crispr.edit(clone.genome, Math.floor(Math.random() * 100), 'BEHAVIOR' as unknown as ChromosomeType, 'gaussian');
        // Update prompt on the fly
        this.modifyClonePrompt(id, `Your genetic traits have mutated. ${clone.genome.params.promptMutation}`);
      }
    }

    clone.metadata.status = success ? 'idle' : 'error';
    
    if (clone.metadata.cloneClass === CloneClass.TEMPORARY) {
      this.clones.delete(id);
    } else {
      this.reportResult(id, result);
    }

    if (!success) throw new Error(`Agent ${clone.metadata.name} failed: ${result}`);
    return result;
  }

  // ====================== TRUE MULTI-AGENT DEBATE ======================

  async runDebate(task: string, cloneIds: string[]): Promise<string> {
    logger.info(`[Agent Orchestrator] ⚔️ Initiating Multi-Agent Debate on: "${task.substring(0, 50)}..."`);
    
    // 1. Parallel Execution
    const debateTasks = cloneIds.map(async (id) => {
      const clone = this.clones.get(id);
      if (!clone || clone.metadata.status === 'paused') return `[${id}] Unavailable`;
      
      logger.debug(`[Agent Orchestrator] Agent ${clone.metadata.name} is thinking...`);
      clone.metadata.status = 'working';
      clone.lastActivity = Date.now();
      
      let response = '';
      try {
        for await (const chunk of clone.engine.query(`DEBATE TOPIC: ${task}\n\nProvide your expert analysis based on your specific persona and tools.`)) {
          if (chunk.type === 'text') response += chunk.content;
        }
      } catch (err) {
        response = `ERROR: ${errorMessage(err)}`;
      }
      clone.metadata.status = 'idle';
      return `### Report from ${clone.metadata.name} (${clone.metadata.cloneClass}):\n${response}\n`;
    });

    const results = await Promise.all(debateTasks);
    
    // 2. Synthesis by Leader
    logger.info(`[Agent Orchestrator] ⚖️ Debate concluded. Orchestrator synthesizing results...`);
    const synthesisPrompt = `You are the ORCHESTRATOR. Your agents have debated the following task:\n\nTASK: ${task}\n\nREPORTS:\n${results.join('\n---\n')}\n\nSynthesize these perspectives into a single, definitive, and optimal solution. Resolve any conflicts logically.`;
    
    let finalSynthesis = '';
    for await (const chunk of this.parentEngine.query(synthesisPrompt)) {
      if (chunk.type === 'text') finalSynthesis += chunk.content;
    }

    return finalSynthesis;
  }

  private async processPendingTasks() {
    if (this.pendingTasksQueue.length === 0) return;
    if (this.activeTasksCount >= this.maxConcurrentTasks) return; // Rate limiting

    const task = this.pendingTasksQueue.shift()!;
    const bestClone = Array.from(this.clones.values()).find(c => c.metadata.status === 'idle');

    if (bestClone) {
      this.activeTasksCount++;
      try {
        await this.runCloneTask(bestClone.metadata.id, task.payload as Record<string, unknown>, task);
      } finally {
        this.activeTasksCount--;
      }
    } else {
      // Re-queue if no agent is available
      this.pendingTasksQueue.unshift(task);
    }
  }

  pauseClone(id: string) {
    const clone = this.clones.get(id);
    if (clone) {
      clone.metadata.status = 'paused';
      logger.info(`[Agent Orchestrator] ⏸️ Agent ${id} PAUSED.`);
    }
  }

  resumeClone(id: string) {
    const clone = this.clones.get(id);
    if (clone && clone.metadata.status === 'paused') {
      clone.metadata.status = 'idle';
      logger.info(`[Agent Orchestrator] ▶️ Agent ${id} RESUMED.`);
    }
  }

  public async terminateClone(cloneId: string, reason: string = 'Task completed'): Promise<void> {
    const clone = this.clones.get(cloneId);
    if (!clone) return;

    logger.info(`[CloneCoordinator] 🛑 Terminating clone: ${cloneId}. Reason: ${reason}`);

    // Notification LegionEngine
    if (clone.metadata.sovereignParent) {
      await this.legionEngine.killBySovereign(clone.metadata.sovereignParent, cloneId, reason);
    }

    if (clone.assignedSpiderNodeId) {
      this.spiderWeb.vacateNode(clone.assignedSpiderNodeId);
    }
    if (this.clones.delete(cloneId)) {
      logger.debug(`[Agent Orchestrator] 💀 Agent ${cloneId} TERMINATED.`);
    }
  }

  killClone(id: string) {
    const clone = this.clones.get(id);
    if (clone?.assignedSpiderNodeId) {
      this.spiderWeb.vacateNode(clone.assignedSpiderNodeId);
    }
    if (this.clones.delete(id)) {
      logger.debug(`[Agent Orchestrator] 💀 Agent ${id} TERMINATED.`);
    }
  }

  modifyClonePrompt(id: string, newInstruction: string) {
    const clone = this.clones.get(id);
    if (clone) {
      clone.engine.setSystemPrompt(clone.engine.getSystemPrompt() + `\n\n[ADMIN UPDATE]: ${newInstruction}`);
      logger.info(`[Agent Orchestrator] ⚡ Agent ${id} instructions MODIFIED.`);
    }
  }

  private reportResult(id: string, result: string) {
    const clone = this.clones.get(id);
    logger.info(`[Task Result] From ${clone?.metadata.name} (${id}): ${result.substring(0, 100)}...`);
    this.emit('task:completed', { agentId: id, result });
  }

  private broadcastOrder(order: string) {
    for (const [id, clone] of this.clones.entries()) {
      if (clone.metadata.status !== 'paused') {
        this.enqueueTask({
          id: randomUUID(),
          cloneId: id,
          payload: order,
          type: 'orchestrator_directive',
          priority: 10,
          requiresConsensus: false,
          requiresSpiderPower: false
        });
      }
    }
  }

  listClones() {
    return Array.from(this.clones.values()).map(c => c.metadata);
  }

  getRealTimeDashboard(): RealTimeDashboard {
    const active = Array.from(this.clones.values()).filter(c => c.metadata.status === 'working').length;
    return {
      timestamp: Date.now(),
      totalClones: this.clones.size,
      activeClones: active,
      harvestedPower: this.getSpiderHarvestedPower(),
      hierarchyDepth: Math.max(...Array.from(this.clones.values()).map(c => c.hierarchyLevel), 0),
      activeParallelGroups: 0,
      pendingTasks: this.pendingTasksQueue.length,
      topContributors: []
    };
  }

  private broadcastRealTimeDashboard() {
    this.emit('dashboard:update', this.getRealTimeDashboard());
  }

  async deploySpiderNode(deviceInfo: { os: string, type: 'phone' | 'pc' | 'iot' | 'edge', gpuPower: number }): Promise<string> {
    const id = `spd_${Math.random().toString(36).slice(2, 8)}`;
    const node: ISpiderNode = {
      id,
      os: String(deviceInfo.os ?? 'unknown'),
      deviceType: (deviceInfo.type === 'edge' ? 'iot' : deviceInfo.type) as 'phone' | 'pc' | 'iot',
      gpuPower: deviceInfo.gpuPower,
      isConnected: true,
      lastSeen: Date.now(),
      latency: Math.random() * 50,
      vramUsage: 0.1,
      capacites: ['inference']
    };
    this.spiderWeb.registerNode(node);
    await this.createClone(`Spider-${id}`, `Compute harvester on ${deviceInfo.os}`, CloneClass.SPIDER, id);
    return id;
  }

  async remoteRecodeSpider(id: string, updates: Partial<ISpiderNode>) {
    this.spiderWeb.updateNodeData(id, updates);
    logger.info(`[Agent Orchestrator] 🕸️ Remote payload sent to Spider ${id}.`);
  }

  getSpiderHarvestedPower(): number {
    return this.spiderWeb.getTotalHarvestedPower();
  }

  getSpiderWeb(): SpiderWeb {
    return this.spiderWeb;
  }
}
