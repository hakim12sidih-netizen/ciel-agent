import logger from '../../utils/logger.js';
import { CloneClass, SovereignStatus, CloneMetadata } from './CloneTypes.js';
import { TitanEcosystem } from '../../evolution/TitanEcosystem.js';

export interface SovereignLineage {
  sovereignName: string;
  status: SovereignStatus;
  maxClones: number;
  emergencyQuota: number;

  clones: Map<string, CloneMetadata>;
  cloneQueue: Array<{ class: CloneClass; mission: string; kwargs: unknown; timestamp: number }>;

  totalSpawned: number;
  totalKilled: number;
  peakConcurrent: number;

  allies: string[];
}

export class LegionEngine {
  private ecosystem: TitanEcosystem;
  public lineages: Map<string, SovereignLineage> = new Map();
  public clones: Map<string, CloneMetadata> = new Map();

  private globalCloneLimit = 231; // 21 * 11
  private hardLimit = 300;

  constructor(ecosystem: TitanEcosystem) {
    this.ecosystem = ecosystem;

    // Initialisation des lignées pour les 21 souverains
    for (const name of Array.from(this.ecosystem.agents.keys())) {
      this.lineages.set(name, {
        sovereignName: name,
        status: SovereignStatus.ACTIVE,
        maxClones: 10,
        emergencyQuota: 3,
        clones: new Map(),
        cloneQueue: [],
        totalSpawned: 0,
        totalKilled: 0,
        peakConcurrent: 0,
        allies: []
      });
    }

    this.setupAlliances();
    logger.info(`[LegionEngine] 👑 Moteur de la Légion initialisé (Capacité: ${this.globalCloneLimit} entités).`);
  }

  private setupAlliances() {
    const alliances: Record<string, string[]> = {
      'ZEUS': ['APOLLON', 'ATHENA', 'POSEIDON'],
      'ATHENA': ['ZEUS', 'APOLLON', 'HYDRA'],
      'HEPHAISTOS': ['ATHENA', 'PROMETHEE', 'HECATE'],
      'TARTARE': ['ZEUS', 'NEMESIS', 'THANATOS'],
      'DIONYSOS': ['MORPHEE', 'PSYCHE', 'ERIS'],
      'HADES': ['THANATOS', 'TARTARE', 'NEMESIS'],
      'PROTEUS': ['ZEUS', 'HECATE', 'TARTARE']
      // Les autres auront ZEUS par défaut
    };

    for (const [sovereign, allies] of Object.entries(alliances)) {
      if (this.lineages.has(sovereign)) {
        this.lineages.get(sovereign)!.allies = allies;
      }
    }
  }

  public async spawnBySovereign(
    sovereignName: string,
    cloneClass: CloneClass,
    mission: string,
    kwargs: unknown = {}
  ): Promise<CloneMetadata | null> {

    if (!this.lineages.has(sovereignName)) {
      throw new Error(`Souverain inconnu: ${sovereignName}`);
    }

    const lineage = this.lineages.get(sovereignName)!;

    // VÉRIFICATION 1: Souverain mort
    if (lineage.status === SovereignStatus.DEAD) {
      logger.warn(`☠️ ${sovereignName} est mort. Adoption de l'orphelin...`);
      return await this.adoptOrphan(sovereignName, cloneClass, mission, kwargs);
    }

    // VÉRIFICATION 2: Quota atteint
    const currentCount = lineage.clones.size;
    const maxAllowed = lineage.maxClones + (lineage.status === SovereignStatus.CRITICAL ? lineage.emergencyQuota : 0);

    if (currentCount >= maxAllowed) {
      if (cloneClass === CloneClass.TEMPORARY && currentCount < maxAllowed + 5) {
        logger.warn(`⚠️ ${sovereignName}: Quota dépassé pour TEMPORARY d'urgence`);
      } else {
        logger.warn(`🚫 ${sovereignName}: Quota ${currentCount}/${maxAllowed} atteint. Mise en file d'attente.`);
        lineage.cloneQueue.push({ class: cloneClass, mission, kwargs, timestamp: Date.now() });
        return null;
      }
    }

    // VÉRIFICATION 3: Limite Globale
    if (this.clones.size >= this.globalCloneLimit) {
      logger.warn(`🌍 Limite globale ${this.clones.size}/${this.globalCloneLimit} atteinte. Déclenchement culling.`);
      await this.globalCulling();
      if (this.clones.size >= this.globalCloneLimit) return null;
    }

    // VÉRIFICATION 4: Némésis Veto
    if ([CloneClass.SPIDER, CloneClass.PAVION, CloneClass.ORCHESTRATOR].includes(cloneClass)) {
      if (!(await this.nemesisCheck(sovereignName, cloneClass))) {
        logger.warn(`⚖️ NÉMÉSIS a mis son veto sur ce clone.`);
        return null;
      }
    }

    // SPAWN AUTORISÉ
    const cloneId = `clone-${sovereignName}-${Date.now().toString().slice(-6)}`;
    const clone: CloneMetadata = {
      id: cloneId,
      name: `${sovereignName}-${cloneClass}-${Date.now().toString().slice(-4)}`,
      purpose: mission,
      status: 'idle',
      cloneClass,
      createdAt: Date.now(),
      sovereignParent: sovereignName,
      fitness: 1.0 // Initial fitness
    };

    lineage.clones.set(cloneId, clone);
    this.clones.set(cloneId, clone);

    lineage.totalSpawned++;
    lineage.peakConcurrent = Math.max(lineage.peakConcurrent, lineage.clones.size);

    logger.info(`✅ ${sovereignName}: Clone ${cloneId} engendré (${lineage.clones.size}/${maxAllowed})`);
    return clone;
  }

  public async killBySovereign(sovereignName: string, cloneId: string, reason: string = 'Sovereign decree'): Promise<boolean> {
    const lineage = this.lineages.get(sovereignName);
    if (!lineage || !lineage.clones.has(cloneId)) return false;

    // Tuer le clone
    logger.info(`🔪 ${sovereignName} tue le clone ${cloneId} (${reason})`);
    lineage.clones.delete(cloneId);
    this.clones.delete(cloneId);
    lineage.totalKilled++;

    // Traiter la file d'attente
    await this.processQueue(sovereignName);
    return true;
  }

  private async processQueue(sovereignName: string) {
    const lineage = this.lineages.get(sovereignName)!;
    while (lineage.cloneQueue.length > 0 && lineage.clones.size < lineage.maxClones) {
      const queued = lineage.cloneQueue.shift();
      logger.info(`📋 ${sovereignName}: Traitement file d'attente...`);
      await this.spawnBySovereign(sovereignName, queued.class, queued.mission, queued.kwargs);
    }
  }

  private async adoptOrphan(deadSovereign: string, cloneClass: CloneClass, mission: string, kwargs: unknown): Promise<CloneMetadata | null> {
    const lineage = this.lineages.get(deadSovereign)!;

    for (const allyName of lineage.allies) {
      const allyLineage = this.lineages.get(allyName);
      if (allyLineage && allyLineage.status === SovereignStatus.ACTIVE && allyLineage.clones.size < allyLineage.maxClones) {
        logger.info(`🏠 ${allyName} adopte un clone orphelin de ${deadSovereign}`);
        return await this.spawnBySovereign(allyName, cloneClass, `[Orphelin de ${deadSovereign}] ${mission}`, kwargs);
      }
    }

    logger.warn(`🦅 Clone orphelin devient FREE autonome sous la direction de ZEUS`);
    return await this.spawnBySovereign('ZEUS', CloneClass.FREE, mission, kwargs);
  }

  private async nemesisCheck(sovereign: string, cc: CloneClass): Promise<boolean> {
    const lineage = this.lineages.get(sovereign)!;
    let dangerous = 0;
    lineage.clones.forEach(c => {
      if (c.cloneClass === CloneClass.SPIDER || c.cloneClass === CloneClass.PAVION) dangerous++;
    });

    if (dangerous >= 3 && (cc === CloneClass.SPIDER || cc === CloneClass.PAVION)) {
      return false; // Veto
    }
    return true;
  }

  private async globalCulling() {
    logger.warn(`🌍 CULLING GLOBAL: ${this.clones.size} clones → cible ${this.globalCloneLimit - 20}`);
    const victims: { id: string, reason: string }[] = [];

    // 1. TEMPORARY vieux (> 5 min)
    this.clones.forEach((clone, cid) => {
      if (clone.cloneClass === CloneClass.TEMPORARY && (Date.now() - clone.createdAt) > 300000) {
        victims.push({ id: cid, reason: 'old_temporary' });
      }
    });

    // 2. Low Fitness
    this.clones.forEach((clone, cid) => {
      if (clone.fitness && clone.fitness < 0.1) {
        victims.push({ id: cid, reason: 'low_fitness' });
      }
    });

    const target = this.globalCloneLimit - 20;
    const toKill = Math.max(0, this.clones.size - target);

    for (let i = 0; i < Math.min(victims.length, toKill); i++) {
      const v = victims[i];
      const clone = this.clones.get(v.id)!;
      await this.killBySovereign(clone.sovereignParent!, v.id, `Global culling: ${v.reason}`);
    }
  }

  public getLineageReport(sovereignName?: string): Record<string, unknown> {
    if (sovereignName) {
      const lin = this.lineages.get(sovereignName)!;
      return {
        sovereign: sovereignName,
        status: lin.status,
        clonesActive: lin.clones.size,
        clonesQueued: lin.cloneQueue.length,
        totalSpawned: lin.totalSpawned,
        totalKilled: lin.totalKilled,
        peakConcurrent: lin.peakConcurrent
      };
    }

    const report: Record<string, unknown> = {
      totalSovereigns: this.lineages.size,
      totalClonesActive: this.clones.size,
      utilization: this.clones.size / this.globalCloneLimit,
      lineages: {}
    };

    this.lineages.forEach((_, name) => {
      report.lineages[name] = this.getLineageReport(name);
    });

    return report;
  }
}
