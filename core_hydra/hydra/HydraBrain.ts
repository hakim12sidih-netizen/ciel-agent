import logger from '../../utils/logger.js';
import { GlobalTitanNVM } from '../../nvm/TitanNVM.js';
import { CortexAssembler } from './CortexLayers.js';
import { Hippocampus } from './Hippocampus.js';
import { ReasoningEngine } from '../ReasoningEngine.js';
import { SemanticEncoder } from './SemanticEncoder.js';

export enum CortexType {
  EXECUTIVE = 'executive',
  MOTOR = 'motor',
  LIMBIC = 'limbic',
  PARIETAL = 'parietal',
  TEMPORAL = 'temporal',
  PREFRONTAL = 'prefrontal',
  CEREBELLAR = 'cerebellar',
  RETICULAR = 'reticular'
}

export enum ExpertCategory {
  CODE = 'code',
  REASONING = 'reasoning',
  LANGUAGE = 'language',
  SYSTEM = 'system',
  CREATIVITY = 'creativity',
  MEMORY = 'memory',
  EMOTION = 'emotion',
  METACOGNITION = 'metacognition'
}

export interface BrainConfig {
  d_model: number;
  n_layers: number;
  n_experts: number;
  n_active_experts: number;
  context_window: number;
}

export interface HydraThought {
  thought_process: string;
  active_cortexes: number[];
  confidence: number;
  content: string;
  response: string;
  retrieved_context: Array<{ id: string; source?: string; score?: number }>;
  model_status: string;
}

export class HydraBrain {
  private config: BrainConfig = {
    d_model: 16384,
    n_layers: 128,
    n_experts: 256,
    n_active_experts: 8,
    context_window: 4194304
  };

  private cortexWeights: Map<CortexType, number> = new Map();
  private activeExperts: Set<number> = new Set();
  private expertMapping: Map<ExpertCategory, number[]> = new Map();
  private assembler: CortexAssembler;
  private hippocampus: Hippocampus;
  private reasoningEngine: ReasoningEngine;

  constructor() {
    this.initializeCortexes();
    this.initializeExperts();
    this.assembler = new CortexAssembler();
    this.hippocampus = new Hippocampus();
    this.reasoningEngine = new ReasoningEngine();
    logger.info('[HYDRA-BRAIN] Orchestrateur neuronal + ReasoningEngine (7 modes) initialisés.');
  }

  public getHippocampus(): Hippocampus {
    return this.hippocampus;
  }

  public async think(prompt: string, context: Record<string, unknown> = {}): Promise<HydraThought> {
    logger.info(`[HYDRA-BRAIN] Analyse de l'intention: "${prompt.slice(0, 80)}"`);

    await this.activateCortex([CortexType.RETICULAR, CortexType.PARIETAL]);

    const experts = this.routeExperts(prompt);
    await this.loadExperts(experts);

    await this.activateCortex([CortexType.EXECUTIVE, CortexType.PREFRONTAL]);
    await this.assembler.process(prompt, this.activeExperts);

    // ── RÉEL : Appel au ReasoningEngine pour un raisonnement structuré ──
    const reasoningResult = await this.reasoningEngine.autoReason({
      query: prompt,
      context: context?.intent?.tags?.join(', ') ?? 'general',
      evidence: context?.pastResults ?? [],
    });
    logger.info(`[HYDRA-BRAIN] 🧠 Mode de raisonnement: ${reasoningResult.type} (confiance: ${(reasoningResult.confidence * 100).toFixed(1)}%)`);

    const retrieved = GlobalTitanNVM.searchKnowledge(prompt, 3);
    const nvmSummary = retrieved.length > 0
      ? retrieved.map((entry) => `${entry.id}`).join(', ')
      : 'aucun';

    // Recherche vectorielle dans l'Hippocampe
    const queryEmbedding = SemanticEncoder.encode(prompt);
    const hippoMemories = await this.hippocampus.retrieve(queryEmbedding, 2);
    const hippoSummary = hippoMemories.length > 0
      ? hippoMemories.map(m => `[Mem:${m.id}]`).join(' ')
      : 'aucune mémoire associative';

    const tags = Array.isArray(context?.intent?.tags) ? context.intent.tags.join(', ') : 'general';
    const content = [
      `[${reasoningResult.type}] ${reasoningResult.conclusion}`,
      `Raisonnement: ${reasoningResult.reasoning.slice(0, 200).trim()}`,
      `Tags: ${tags}`,
      `Experts actifs: ${Array.from(this.activeExperts).join(', ') || 'langage'}`,
      `Contexte NVM: ${nvmSummary} | Hippocampe: ${hippoSummary}`,
      `Mode modele: ${GlobalTitanNVM.getStatus()}`
    ].join('\n');

    // Confiance réelle: pondération entre ReasoningEngine et la richesse du contexte NVM
    const nvmBonus = retrieved.length > 0 ? 0.1 : 0;
    const confidence = Math.min(0.98, reasoningResult.confidence + nvmBonus);

    return {
      thought_process: `[${reasoningResult.type}] ${this.activeExperts.size} experts actifs, ${retrieved.length} souvenirs NVM, confiance=${(confidence * 100).toFixed(1)}%.`,
      active_cortexes: Array.from(this.activeExperts),
      confidence,
      content,
      response: content,
      retrieved_context: retrieved.map((entry) => ({ id: entry.id, source: entry.source, score: entry.score })),
      model_status: GlobalTitanNVM.getStatus()
    };
  }

  public async encodeInput(type: 'vision' | 'audio' | 'ast' | 'text', data: string | Buffer) {
    logger.debug(`[HYDRA-BRAIN] Encodage ${type}.`);
    return { type, bytes: typeof data === 'string' ? data.length : 0 };
  }

  public async dreamPhase() {
    logger.info('[HYDRA-BRAIN] Cycle de self-play local lance.');
    await new Promise(r => setTimeout(r, 2000));
    logger.info("[HYDRA-BRAIN] Cycle termine. Aucun poids de modele n'a ete modifie sans backend d'entrainement.");
  }

  public async onlineLearn(interaction: Record<string, unknown>, success: boolean) {
    const feedback = success ? 'positive' : 'correction';
    await GlobalTitanNVM.appendToNvm(
      `interaction_${Date.now()}`,
      JSON.stringify({ interaction, success, feedback }),
      'online_learning'
    );
  }

  public getStatus() {
    const nvm = GlobalTitanNVM.getStats();
    return {
      target_parameters: '1.1T',
      actual_model: nvm.modelLoaded ? 'external_weights_loaded' : 'not_loaded',
      layers: this.config.n_layers,
      active_experts: Array.from(this.activeExperts),
      nvm,
      cortex_health: 'operational'
    };
  }

  private initializeExperts() {
    const categories = Object.values(ExpertCategory);
    categories.forEach((cat, idx) => {
      const start = idx * 32;
      this.expertMapping.set(cat, Array.from({ length: 32 }, (_, i) => start + i));
    });
  }

  private initializeCortexes() {
    this.cortexWeights.set(CortexType.EXECUTIVE, 200);
    this.cortexWeights.set(CortexType.MOTOR, 150);
    this.cortexWeights.set(CortexType.LIMBIC, 100);
    this.cortexWeights.set(CortexType.PARIETAL, 80);
    this.cortexWeights.set(CortexType.TEMPORAL, 150);
    this.cortexWeights.set(CortexType.PREFRONTAL, 120);
    this.cortexWeights.set(CortexType.CEREBELLAR, 100);
    this.cortexWeights.set(CortexType.RETICULAR, 50);
  }

  private routeExperts(input: string): number[] {
    const selected: number[] = [];
    const lower = input.toLowerCase();

    if (/code|script|program|rust|python|api|typescript/.test(lower)) {
      selected.push(...this.getExpertsFromCategory(ExpertCategory.CODE, 2));
    }
    if (/analys|logique|calcul|math|pourquoi|risque/.test(lower)) {
      selected.push(...this.getExpertsFromCategory(ExpertCategory.REASONING, 2));
    }
    if (/fichier|process|system|os|registre|dossier/.test(lower)) {
      selected.push(...this.getExpertsFromCategory(ExpertCategory.SYSTEM, 2));
    }
    if (/souvien|memoire|historique|passe|nvm/.test(lower)) {
      selected.push(...this.getExpertsFromCategory(ExpertCategory.MEMORY, 2));
    }
    if (/cree|art|image|music|story/.test(lower)) {
      selected.push(...this.getExpertsFromCategory(ExpertCategory.CREATIVITY, 2));
    }
    if (/sens|humeur|triste|content|empathie/.test(lower)) {
      selected.push(...this.getExpertsFromCategory(ExpertCategory.EMOTION, 2));
    }
    if (/auto|reflexion|corrige|verite|repare/.test(lower)) {
      selected.push(...this.getExpertsFromCategory(ExpertCategory.METACOGNITION, 2));
    }

    selected.push(...this.getExpertsFromCategory(ExpertCategory.LANGUAGE, 2));
    return [...new Set(selected)].slice(0, this.config.n_active_experts);
  }

  private getExpertsFromCategory(cat: ExpertCategory, count: number): number[] {
    const pool = this.expertMapping.get(cat) || [];
    return [...pool].sort(() => Math.random() - 0.5).slice(0, count);
  }

  private async activateCortex(types: CortexType[]) {
    for (const type of types) {
      const weight = this.cortexWeights.get(type) || 50;
      logger.debug(`[HYDRA-BRAIN] Activation cortex ${type} (${weight}B cible).`);
      GlobalTitanNVM.accessLayer(this.getCortexLayerId(type), 0, weight * 1024);
    }
  }

  private async loadExperts(expertIds: number[]) {
    this.activeExperts.clear();
    for (const id of expertIds) {
      this.activeExperts.add(id);
      GlobalTitanNVM.accessLayer(21, id * 100, 500);
    }
    logger.debug(`[HYDRA-BRAIN] Experts charges: [${expertIds.join(', ')}]`);
  }

  private getCortexLayerId(type: CortexType): number {
    const mapping: Record<CortexType, number> = {
      [CortexType.EXECUTIVE]: 0,
      [CortexType.MOTOR]: 1,
      [CortexType.LIMBIC]: 2,
      [CortexType.PARIETAL]: 3,
      [CortexType.TEMPORAL]: 4,
      [CortexType.PREFRONTAL]: 5,
      [CortexType.CEREBELLAR]: 6,
      [CortexType.RETICULAR]: 7
    };
    return mapping[type];
  }
}
