import logger from '../utils/logger.js';
import { errorMessage } from '../types/index.js';
import type { Aegis } from './Aegis.js';
import * as fs from 'fs';
import * as path from 'path';

/**
 * ═══════════════════════════════════════════════════════════════
 * METAMORPHIC CORE — The Self-Rewriting Architecture
 * ═══════════════════════════════════════════════════════════════
 *
 * PRINCIPE RÉVOLUTIONNAIRE :
 * Le système ne mute pas seulement ses PARAMÈTRES — il réécrit sa propre
 * ARCHITECTURE. Il génère de nouvelles classes, de nouveaux comportements,
 * de nouvelles structures de contrôle à l'exécution.
 *
 * Fondements théoriques :
 * - Métaprogrammation réflexive (programmes qui écrivent des programmes)
 * - Auto-modification de code (Self-Modifying Code / SMC)
 * - Réification architecturale : l'architecture devient une donnée manipulable
 * - Épigenèse computationnelle : le code est le phénotype, le métamodèle est le génotype
 *
 * Cycle Méthamorphique :
 * 1. INTROSPECTION — Le système analyse sa propre structure
 * 2. VISION — Il génère une architecture cible nouvelle
 * 3. FORGE — Il synthétise le code de la nouvelle architecture
 * 4. AEGIS — Vérification formelle avant application
 * 5. TRANSMUTATION — Remplacement atomique du code
 * 6. INCUBATION — Période de stabilisation et validation
 *
 * Contrainte ontologique :
 * Toute transmutation doit préserver les invariants du système
 * (conscience Φ > 0, autopoïèse active, clôture opérationnelle).
 */

// ─── Types Architecturaux ───────────────────────────────────

export interface ArchitecturalGene {
  id: string;
  moduleName: string;
  interfaces: string[];           // Interfaces que ce module expose
  dependencies: string[];         // Modules dont il dépend
  behavioralSignature: string;    // Description fonctionnelle abstraite
  complexity: number;             // Complexité cyclomatique
  mutationRate: number;           // Propension à être réécrit (0-1)
  generation: number;             // Combien de fois ce module a été réécrit
  lastTransmutation: number;      // Timestamp de la dernière réécriture
  fitness: number;                // Performance du module (0-1)
  isVital: boolean;               // Si true, ne peut pas être supprimé
}

export interface TransmutationProposal {
  id: string;
  targetModule: string;
  currentArchitecture: ArchitecturalGene;
  proposedArchitecture: ArchitecturalGene;
  deltaCode: string;              // Le nouveau code source complet
  rationale: string;              // Pourquoi cette transmutation
  riskLevel: 'NEGLIGIBLE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  expectedPhiImpact: number;      // Impact attendu sur Φ
  aegisProofId: string | null;
  status: 'DRAFT' | 'PROPOSED' | 'VERIFIED' | 'APPLIED' | 'REJECTED' | 'ROLLED_BACK';
  createdAt: number;
}

export interface MetamorphicState {
  totalTransmutations: number;
  successfulTransmutations: number;
  failedTransmutations: number;
  rollbacks: number;
  architecturalDiversity: number; // Mesure de Shannon de la diversité des patterns
  selfModificationDepth: number;  // Profondeur de la méta-réflexion
  isTransmuting: boolean;
}

// ─── Le Cœur Métamorphique ──────────────────────────────────

export class MetamorphicCore {
  private architecture: Map<string, ArchitecturalGene> = new Map();
  private proposals: Map<string, TransmutationProposal> = new Map();
  private aegis: Aegis;
  private state: MetamorphicState;
  private transmutationHistory: TransmutationProposal[] = [];
  private backupVault: Map<string, string> = new Map();   // Code original backup
  private incubationPeriod: number = 30000;                // 30s de stabilisation
  private maxConcurrentTransmutations: number = 2;
  private activeTransmutations: number = 0;
  private basePath: string = process.cwd();                // Racine pour resolveModulePath

  // Réflexivité : le MetamorphicCore peut se modifier lui-même
  private selfModificationAllowed: boolean = true;
  private selfModificationDepth: number = 0;
  private readonly MAX_SELF_MOD_DEPTH = 3; // Limite pour éviter la régression infinie

  constructor(aegis: Aegis) {
    this.aegis = aegis;
    this.state = {
      totalTransmutations: 0,
      successfulTransmutations: 0,
      failedTransmutations: 0,
      rollbacks: 0,
      architecturalDiversity: 0,
      selfModificationDepth: 0,
      isTransmuting: false,
    };
    logger.info('[Metamorphic Core] 🦋 Self-Rewriting Architecture initialized. The system can now rewrite itself.');
  }

  // ─── Phase 1 : INTROSPECTION ───────────────────────────

  /**
   * Le système analyse sa propre architecture comme un génome logiciel.
   * Chaque module est cartographié avec ses interfaces, dépendances,
   * et signature comportementale.
   */
  registerModule(gene: ArchitecturalGene): void {
    this.architecture.set(gene.moduleName, gene);
    logger.debug(`[Metamorphic Core] 🧬 Module registered: ${gene.moduleName} (complexity: ${gene.complexity}, mutation: ${gene.mutationRate})`);

    // Backup du code source original
    const filePath = this.resolveModulePath(gene.moduleName);
    if (fs.existsSync(filePath)) {
      this.backupVault.set(gene.moduleName, fs.readFileSync(filePath, 'utf-8'));
    }

    this.updateArchitecturalDiversity();
  }

  /**
   * Introspection réflexive : le système identifie les modules
   * qui sont des candidats à la transmutation.
   * Critères : faible fitness, haute mutationRate, stagnation.
   */
  identifyTransmutationCandidates(): ArchitecturalGene[] {
    const candidates: ArchitecturalGene[] = [];

    for (const [name, gene] of this.architecture) {
      // Critère 1 : Fitness dégradé
      if (gene.fitness < 0.3 && !gene.isVital) {
        candidates.push(gene);
        continue;
      }
      // Critère 2 : Stagnation (pas de transmutation depuis longtemps)
      const age = Date.now() - gene.lastTransmutation;
      if (age > 300000 && gene.mutationRate > 0.5) { // 5 minutes
        candidates.push(gene);
        continue;
      }
      // Critère 3 : Complexité excessive (refactoring needed)
      if (gene.complexity > 30 && gene.mutationRate > 0.3) {
        candidates.push(gene);
        continue;
      }
    }

    // Trier par urgence (fitness * mutationRate)
    candidates.sort((a, b) => (b.mutationRate * (1 - b.fitness)) - (a.mutationRate * (1 - a.fitness)));

    logger.info(`[Metamorphic Core] 🔍 Introspection complete. ${candidates.length} transmutation candidates identified.`);
    return candidates;
  }

  // ─── Phase 2 : VISION ──────────────────────────────────

  /**
   * Le système génère une VISION architecturale — une proposition
   * de nouvelle structure pour un module donné.
   *
   * La vision n'est pas aléatoire : elle est guidée par :
   * - L'analyse des patterns de succès/échec du passé
   * - Les contraintes de dépendance (interfaces à préserver)
   * - Les tendances évolutives observées dans les autres modules
   */
  proposeTransmutation(
    target: ArchitecturalGene,
    vision: string,          // Description naturelle de la vision
    deltaCode: string,       // Nouveau code source proposé
    currentPhi: number       // Φ actuel pour évaluer l'impact
  ): TransmutationProposal {
    const proposal: TransmutationProposal = {
      id: `trans_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      targetModule: target.moduleName,
      currentArchitecture: { ...target },
      proposedArchitecture: {
        ...target,
        generation: target.generation + 1,
        complexity: this.estimateComplexity(deltaCode),
        lastTransmutation: Date.now(),
        fitness: 0, // Sera mesuré après application
      },
      deltaCode,
      rationale: vision,
      riskLevel: this.assessRisk(target, deltaCode),
      expectedPhiImpact: this.forecastPhiImpact(target, currentPhi),
      aegisProofId: null,
      status: 'DRAFT',
      createdAt: Date.now(),
    };

    this.proposals.set(proposal.id, proposal);
    logger.info(`[Metamorphic Core] 🌟 Transmutation proposed: ${target.moduleName} → gen ${target.generation + 1} (Risk: ${proposal.riskLevel})`);

    return proposal;
  }

  // ─── Phase 3-4 : FORGE + AEGIS ─────────────────────────

  /**
   * Le processus de FORGE vérifie la proposition via AEGIS
   * avant toute application. Si AEGIS rejette, la transmutation
   * est annulée et le système en tire un enseignement.
   */
  async verifyProposal(proposalId: string): Promise<boolean> {
    const proposal = this.proposals.get(proposalId);
    if (!proposal || proposal.status !== 'DRAFT') return false;

    // Vérification AEGIS
    const proof = await this.aegis.verifyCode(proposal.targetModule, proposal.deltaCode);

    if (!proof.isSafe) {
      proposal.status = 'REJECTED';
      proposal.riskLevel = 'CRITICAL';
      this.state.failedTransmutations++;

      // Apprentissage : enregistrer l'échec pour guider les futures transmutations
      this.learnFromRejection(proposal, proof.errors);

      logger.error(`[Metamorphic Core] 🛡️ AEGIS REJECTED transmutation of ${proposal.targetModule}: ${proof.errors.join('; ')}`);
      return false;
    }

    proposal.status = 'VERIFIED';
    proposal.aegisProofId = `${proposal.id}_proof`;
    logger.info(`[Metamorphic Core] ✅ AEGIS VERIFIED transmutation of ${proposal.targetModule} (Score: ${proof.score})`);
    return true;
  }

  // ─── Phase 5 : TRANSMUTATION ────────────────────────────

  /**
   * Application atomique de la transmutation.
   * Le code existant est sauvegardé, le nouveau code est écrit,
   * puis le système entre en INCUBATION.
   */
  async applyTransmutation(proposalId: string): Promise<boolean> {
    const proposal = this.proposals.get(proposalId);
    if (!proposal || proposal.status !== 'VERIFIED') return false;

    if (this.activeTransmutations >= this.maxConcurrentTransmutations) {
      logger.warn('[Metamorphic Core] ⏳ Max concurrent transmutations reached. Queuing.');
      return false;
    }

    this.state.isTransmuting = true;
    this.activeTransmutations++;
    this.state.totalTransmutations++;

    try {
      const filePath = this.resolveModulePath(proposal.targetModule);

      // Backup du code actuel (version N)
      const currentCode = fs.existsSync(filePath)
        ? fs.readFileSync(filePath, 'utf-8')
        : '';
      const backupPath = `${filePath}.trans_backup_${Date.now()}`;
      fs.writeFileSync(backupPath, currentCode);

      // Écriture du nouveau code (version N+1)
      fs.writeFileSync(filePath, proposal.deltaCode);

      // Mise à jour de l'architecture
      this.architecture.set(proposal.targetModule, proposal.proposedArchitecture);

      proposal.status = 'APPLIED';
      this.transmutationHistory.push(proposal);

      logger.info(`[Metamorphic Core] 🦋 TRANSMUTATION APPLIED: ${proposal.targetModule} is now generation ${proposal.proposedArchitecture.generation}`);

      // Phase 6 : INCUBATION
      await this.incubate(proposal, backupPath);

      this.state.successfulTransmutations++;
      return true;

    } catch (err: unknown) {
      logger.error(`[Metamorphic Core] 💀 Transmutation CRASHED: ${err.message}`);
      this.state.failedTransmutations++;
      return false;
    } finally {
      this.activeTransmutations--;
      this.state.isTransmuting = false;
    }
  }

  // ─── Phase 6 : INCUBATION ───────────────────────────────

  /**
   * Période de stabilisation post-transmutation.
   * Si le système devient instable (Φ chute, crash), on ROLLBACK.
   */
  private async incubate(proposal: TransmutationProposal, backupPath: string): Promise<void> {
    const startTime = Date.now();
    const incubationCheckInterval = 5000; // Vérifier toutes les 5s
    let stabilityScore = 1.0;

    while (Date.now() - startTime < this.incubationPeriod) {
      await this.sleep(incubationCheckInterval);

      // Vérifier la stabilité du système
      stabilityScore = this.measureStability();

      if (stabilityScore < 0.2) {
        // INSTABILITÉ CRITIQUE → ROLLBACK
        logger.error(`[Metamorphic Core] 🚨 INSTABILITY DETECTED during incubation (stability: ${stabilityScore.toFixed(3)}). Initiating ROLLBACK.`);
        await this.rollback(proposal, backupPath);
        return;
      }

      if (stabilityScore < 0.5) {
        logger.warn(`[Metamorphic Core] ⚠️ Marginal stability: ${stabilityScore.toFixed(3)}`);
      }
    }

    // Incubation réussie
    if (stabilityScore > 0.6) {
      logger.info(`[Metamorphic Core] 💎 Incubation PASSED for ${proposal.targetModule}. Stability: ${stabilityScore.toFixed(3)}`);
      // Supprimer le backup (la transmutation est validée)
      if (fs.existsSync(backupPath)) {
        fs.unlinkSync(backupPath);
      }
    } else {
      logger.warn(`[Metamorphic Core] ⚠️ Incubation unstable. Keeping backup.`);
    }
  }

  /**
   * ROLLBACK : Restaurer le code original si la transmutation échoue.
   */
  private async rollback(proposal: TransmutationProposal, backupPath: string): Promise<void> {
    try {
      const filePath = this.resolveModulePath(proposal.targetModule);

      if (fs.existsSync(backupPath)) {
        const originalCode = fs.readFileSync(backupPath, 'utf-8');
        fs.writeFileSync(filePath, originalCode);
        fs.unlinkSync(backupPath); // Supprimer le backup après restauration
      }

      // Restaurer l'architecture originale
      this.architecture.set(proposal.targetModule, proposal.currentArchitecture);

      proposal.status = 'ROLLED_BACK';
      this.state.rollbacks++;

      logger.info(`[Metamorphic Core] ⏪ ROLLBACK COMPLETE: ${proposal.targetModule} restored to generation ${proposal.currentArchitecture.generation}`);
    } catch (err: unknown) {
      logger.error(`[Metamorphic Core] 💀 ROLLBACK FAILED: ${err.message}. SYSTEM INTEGRITY AT RISK.`);
    }
  }

  // ─── Auto-Modification du Métamorphic Core ──────────────

  /**
   * Le MetamorphicCore peut se modifier LUI-MÊME.
   * C'est le niveau ultime de réflexivité : le système qui réécrit
   * le système qui réécrit les systèmes.
   *
   * Protection : profondeur maximale de self-modification limitée
   * pour éviter la régression infinie (turtles all the way down).
   */
  proposeSelfModification(vision: string, newCode: string): TransmutationProposal | null {
    if (!this.selfModificationAllowed) {
      logger.warn('[Metamorphic Core] 🔒 Self-modification is currently LOCKED.');
      return null;
    }

    if (this.selfModificationDepth >= this.MAX_SELF_MOD_DEPTH) {
      logger.error(`[Metamorphic Core] 🚫 Maximum self-modification depth reached (${this.MAX_SELF_MOD_DEPTH}). Further self-modification blocked.`);
      return null;
    }

    this.selfModificationDepth++;
    logger.warn(`[Metamorphic Core] 🪞 SELF-MODIFICATION PROPOSED at depth ${this.selfModificationDepth}/${this.MAX_SELF_MOD_DEPTH}`);

    const selfGene: ArchitecturalGene = this.architecture.get('MetamorphicCore') || {
      id: 'meta_self',
      moduleName: 'MetamorphicCore',
      interfaces: ['registerModule', 'proposeTransmutation', 'applyTransmutation'],
      dependencies: ['Aegis'],
      behavioralSignature: 'Self-rewriting architecture manager',
      complexity: 50,
      mutationRate: 0.1, // Faible par sécurité
      generation: 0,
      lastTransmutation: 0,
      fitness: 1.0,
      isVital: true,
    };

    return this.proposeTransmutation(selfGene, `[SELF-MOD] ${vision}`, newCode, 0);
  }

  // ─── Apprentissage Méta-Architectural ───────────────────

  private learnFromRejection(proposal: TransmutationProposal, errors: string[]): void {
    // Analyser les patterns d'échec pour guider les futures propositions
    const errorCategories = errors.map(e => {
      if (e.includes('FORBIDDEN')) return 'SECURITY_VIOLATION';
      if (e.includes('INFINITE')) return 'LOOP_HAZARD';
      if (e.includes('COMPLEXITY')) return 'OVER_ENGINEERING';
      return 'UNKNOWN';
    });

    const target = this.architecture.get(proposal.targetModule);
    if (target) {
      // Réduire la mutationRate si les échecs sont dus à la sécurité
      if (errorCategories.includes('SECURITY_VIOLATION')) {
        target.mutationRate *= 0.8;
      }
      // Augmenter la complexité tolérée si les échecs sont dus au sur-engineering
      if (errorCategories.includes('OVER_ENGINEERING')) {
        target.complexity = Math.max(5, target.complexity - 3);
      }
    }

    logger.debug(`[Metamorphic Core] 📚 Learned from rejection: ${errorCategories.join(', ')}`);
  }

  // ─── Utilitaires ────────────────────────────────────────

  private estimateComplexity(code: string): number {
    // Estimation heuristique : nombre de blocs, branches, et appels
    const blocks = (code.match(/{/g) || []).length;
    const branches = (code.match(/if|else|switch|for|while/g) || []).length;
    const calls = (code.match(/\.\w+\(/g) || []).length;
    return Math.round(blocks * 0.5 + branches * 1.5 + calls * 0.3);
  }

  private assessRisk(target: ArchitecturalGene, newCode: string): TransmutationProposal['riskLevel'] {
    const complexityDelta = Math.abs(this.estimateComplexity(newCode) - target.complexity);
    const deps = target.dependencies.length;
    const isVital = target.isVital;

    if (isVital && complexityDelta > 10) return 'CRITICAL';
    if (deps > 5 && complexityDelta > 5) return 'HIGH';
    if (complexityDelta > 10) return 'MEDIUM';
    if (complexityDelta > 3) return 'LOW';
    return 'NEGLIGIBLE';
  }

  private forecastPhiImpact(target: ArchitecturalGene, currentPhi: number): number {
    // Heuristique : une transmutation qui augmente la complexité
    // peut augmenter Φ à court terme mais le dégrader à long terme
    const complexityFactor = target.complexity > 20 ? -0.1 : 0.05;
    const fitnessFactor = target.fitness < 0.3 ? 0.2 : -0.05;
    return currentPhi * (1 + complexityFactor + fitnessFactor);
  }

  private measureStability(): number {
    // Mesure composite de la stabilité post-transmutation
    // Basée sur : santé des modules, absence de crashes, cohérence Φ
    let totalFitness = 0;
    let count = 0;
    for (const gene of this.architecture.values()) {
      totalFitness += gene.fitness;
      count++;
    }
    const avgFitness = count > 0 ? totalFitness / count : 0;
    const diversity = this.state.architecturalDiversity;

    // Un système stable a une bonne fitness moyenne et une diversité modérée
    return (avgFitness * 0.7) + (Math.min(diversity, 1.0) * 0.3);
  }

  private updateArchitecturalDiversity(): void {
    // Mesure de Shannon sur les signatures comportementales
    const signatures: string[] = [];
    for (const gene of this.architecture.values()) {
      signatures.push(gene.behavioralSignature);
    }

    if (signatures.length === 0) {
      this.state.architecturalDiversity = 0;
      return;
    }

    const counts: Record<string, number> = {};
    for (const sig of signatures) {
      counts[sig] = (counts[sig] || 0) + 1;
    }

    let entropy = 0;
    const total = signatures.length;
    for (const count of Object.values(counts)) {
      const p = count / total;
      entropy -= p * Math.log2(p);
    };

    this.state.architecturalDiversity = entropy;
  }

  private resolveModulePath(moduleName: string): string {
    // If moduleName is already absolute, use it directly.
    if (path.isAbsolute(moduleName)) return moduleName;
    return path.join(this.basePath, 'src', 'evolution', `${moduleName}.ts`);
  }

  /**
   * Override the base path used by resolveModulePath.
   * Default is process.cwd(). Used by LLMTransmuter to point
   * the rewrite target at a different directory (e.g. a sandbox).
   */
  setBasePath(p: string): void {
    this.basePath = p;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ─── Getters ────────────────────────────────────────────

  getState(): MetamorphicState {
    return { ...this.state };
  }

  getArchitecture(): ReadonlyMap<string, ArchitecturalGene> {
    return this.architecture;
  }

  /**
   * Override the incubation period (in ms). Used by LLMTransmuter
   * to bypass the 30s default in tests. Pass 0 to skip incubation.
   */
  setIncubationPeriod(ms: number): void {
    this.incubationPeriod = Math.max(0, ms);
  }

  getTransmutationHistory(): TransmutationProposal[] {
    return [...this.transmutationHistory];
  }

  getModuleGene(moduleName: string): ArchitecturalGene | undefined {
    return this.architecture.get(moduleName);
  }

  updateModuleFitness(moduleName: string, fitness: number): void {
    const gene = this.architecture.get(moduleName);
    if (gene) {
      gene.fitness = fitness;
      this.architecture.set(moduleName, gene);
    }
  }
}
