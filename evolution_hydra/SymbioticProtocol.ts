/**
 * ═══════════════════════════════════════════════════════════════
 * SYMBIOTIC PROTOCOL — Mutualist Super-Organisms
 * ═══════════════════════════════════════════════════════════════
 *
 * PHASE 2 : Refactorisé pour :
 * 1. Utiliser UnifiedGenome au lieu de Genome (V1)
 * 2. Découpler de GeneticAlgorithm via l'interface IGenomeProvider
 * 3. Émettre des événements 'superorganism.created' pour wiring
 *
 * PRINCIPE : L'évolution n'est pas que compétition. Les mutualismes
 * créent des SUPER-ORGANISMES dont la fitness dépasse la somme.
 *
 * Fondements théoriques : symbiogenèse (Margulis), super-organismes
 * (E.O. Wilson), mutualisme obligatoire vs facultatif, endosymbiose.
 */

import { EventEmitter } from 'events';
import logger from '../utils/logger.js';
import type { UnifiedGenome } from './UnifiedGenome.js';
import type { GeneticAlgorithm } from './GeneticAlgorithm.js';

// ─── Types Symbiotiques ─────────────────────────────────────

export enum SymbiosisType {
  COMMENSALISM = 'COMMENSALISM',     // A bénéficie, B neutre
  MUTUALISM = 'MUTUALISM',           // A et B bénéficient
  ENDOSYMBIOSIS = 'ENDOSYMBIOSIS',   // A vit dans B
  CATALYSIS = 'CATALYSIS',           // A accélère B temporairement
}

export enum SymbiosisStatus {
  PROPOSED = 'PROPOSED',
  NEGOTIATING = 'NEGOTIATING',
  ACTIVE = 'ACTIVE',
  STRESSED = 'STRESSED',
  DISSOLVED = 'DISSOLVED',
  EVOLVED = 'EVOLVED',               // La symbiose a produit un nouvel organisme
}

export interface SymbioticPact {
  id: string;
  partnerA: string;               // Genome ID
  partnerB: string;               // Genome ID
  type: SymbiosisType;
  status: SymbiosisStatus;
  fitness: number;                // Fitness combinée du super-organisme
  synergyScore: number;           // Mesure de synergie (1+1>2)
  stability: number;              // Stabilité du pacte (0-1)
  age: number;                    // Durée du pacte
  exchanges: ResourceExchange[];  // Historique des échanges
  complementarity: ComplementarityMap;
  createdAt: number;
  dissolvedAt?: number;
}

export interface ResourceExchange {
  fromId: string;
  toId: string;
  resource: string;
  amount: number;
  timestamp: number;
}

export interface ComplementarityMap {
  aProvidesB: string[];
  bProvidesA: string[];
  sharedStrengths: string[];
  riskAreas: string[];
}

export interface SuperOrganism {
  id: string;
  pactId: string;
  combinedGenome: UnifiedGenome;
  memberIds: string[];
  generation: number;
  fitness: number;
  isViable: boolean;
  createdAt: number;
}

export interface SymbioticState {
  totalPacts: number;
  activePacts: number;
  superOrganisms: number;
  averageSynergy: number;
  dominantSymbiosisType: SymbiosisType;
  symbioticDiversity: number;
  parasitismDetected: number;
}

/**
 * Interface de fournisseur de génomes — découple SymbioticProtocol
 * de GeneticAlgorithm. Tout objet qui expose getPopulation() peut
 * être utilisé.
 */
export interface IGenomeProvider {
  getPopulation(): UnifiedGenome[];
}

// ─── Le Protocole Symbiotique ───────────────────────────────

export class SymbioticProtocol extends EventEmitter {
  private pacts: Map<string, SymbioticPact> = new Map();
  private superOrganisms: Map<string, SuperOrganism> = new Map();
  private provider: IGenomeProvider;
  private state: SymbioticState;

  constructor(provider: IGenomeProvider) {
    super();
    this.provider = provider;
    this.state = {
      totalPacts: 0,
      activePacts: 0,
      superOrganisms: 0,
      averageSynergy: 0,
      dominantSymbiosisType: SymbiosisType.MUTUALISM,
      symbioticDiversity: 0,
      parasitismDetected: 0,
    };

    logger.info('[Symbiotic Protocol] 🤝 Mutualist super-organism engine initialized. Cooperation is as powerful as competition.');
  }

  /**
   * Constructeur rétro-compatible : accepte un GeneticAlgorithm.
   * @deprecated Utilisez le constructeur IGenomeProvider directement.
   */
  static fromGeneticAlgorithm(ga: GeneticAlgorithm): SymbioticProtocol {
    return new SymbioticProtocol({ getPopulation: () => ga.getPopulation() });
  }

  // ─── Détection de Complémentarité ──────────────────────

  analyzeComplementarity(genomeA: UnifiedGenome, genomeB: UnifiedGenome): ComplementarityMap {
    const aProvidesB: string[] = [];
    const bProvidesA: string[] = [];
    const sharedStrengths: string[] = [];
    const riskAreas: string[] = [];

    // 1. Complémentarité des outils
    for (const [tool, weightA] of Object.entries(genomeA.params.toolWeights)) {
      const weightB = genomeB.params.toolWeights[tool] || 1;
      if (weightA > 1.3 && weightB < 0.8) {
        aProvidesB.push(`Tool mastery: ${tool}`);
      } else if (weightB > 1.3 && weightA < 0.8) {
        bProvidesA.push(`Tool mastery: ${tool}`);
      } else if (weightA > 1.3 && weightB > 1.3) {
        sharedStrengths.push(`Shared excellence: ${tool}`);
      }
    }

    // 2. Complémentarité des températures
    if (genomeA.params.temperature > 0.8 && genomeB.params.temperature < 0.4) {
      aProvidesB.push('Creative exploration');
      bProvidesA.push('Rigorous exploitation');
    } else if (genomeB.params.temperature > 0.8 && genomeA.params.temperature < 0.4) {
      bProvidesA.push('Creative exploration');
      aProvidesB.push('Rigorous exploitation');
    }

    // 3. Complémentarité des spécialités
    for (const specA of genomeA.specialties) {
      if (genomeB.specialties.includes(specA)) {
        sharedStrengths.push(`Shared specialty: ${specA}`);
      }
    }
    for (const specA of genomeA.specialties) {
      if (!genomeB.specialties.includes(specA)) {
        aProvidesB.push(`Unique specialty: ${specA}`);
      }
    }
    for (const specB of genomeB.specialties) {
      if (!genomeA.specialties.includes(specB)) {
        bProvidesA.push(`Unique specialty: ${specB}`);
      }
    }

    // 4. Zones de risque
    if (genomeA.params.dockerAffinity < 0.3 && genomeB.params.dockerAffinity < 0.3) {
      riskAreas.push('Infrastructure isolation');
    }
    if (genomeA.params.polyglotDepth < 0.3 && genomeB.params.polyglotDepth < 0.3) {
      riskAreas.push('Multi-language capability');
    }

    return { aProvidesB, bProvidesA, sharedStrengths, riskAreas };
  }

  // ─── Formation de Pactes ───────────────────────────────

  proposePact(genomeA: UnifiedGenome, genomeB: UnifiedGenome): SymbioticPact | null {
    const existingPactA = this.findActivePact(genomeA.id);
    const existingPactB = this.findActivePact(genomeB.id);
    if (existingPactA || existingPactB) return null;

    const complementarity = this.analyzeComplementarity(genomeA, genomeB);

    const synergyGain = complementarity.aProvidesB.length + complementarity.bProvidesA.length;
    const synergyCost = complementarity.riskAreas.length;

    if (synergyGain <= synergyCost + 1) {
      logger.debug(`[Symbiotic Protocol] 🚫 Pact rejected: insufficient complementarity (gain: ${synergyGain}, cost: ${synergyCost})`);
      return null;
    }

    const type = this.determineSymbiosisType(genomeA, genomeB, complementarity);
    const synergyScore = this.computeSynergyScore(genomeA, genomeB, complementarity);

    const pact: SymbioticPact = {
      id: `pact_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`,
      partnerA: genomeA.id,
      partnerB: genomeB.id,
      type,
      status: SymbiosisStatus.PROPOSED,
      fitness: 0,
      synergyScore,
      stability: 0.5,
      age: 0,
      exchanges: [],
      complementarity,
      createdAt: Date.now(),
    };

    this.pacts.set(pact.id, pact);
    this.state.totalPacts++;

    logger.info(`[Symbiotic Protocol] 🤝 Pact PROPOSED: ${genomeA.id} ↔ ${genomeB.id} (${type}, synergy: ${synergyScore.toFixed(2)})`);

    return pact;
  }

  activatePact(pactId: string): boolean {
    const pact = this.pacts.get(pactId);
    if (!pact || pact.status !== SymbiosisStatus.PROPOSED) return false;

    pact.status = SymbiosisStatus.ACTIVE;
    this.state.activePacts++;

    logger.info(`[Symbiotic Protocol] ✅ Pact ACTIVATED: ${pact.partnerA} ↔ ${pact.partnerB}`);
    return true;
  }

  // ─── Échanges de Ressources ────────────────────────────

  executeExchange(pactId: string): void {
    const pact = this.pacts.get(pactId);
    if (!pact || pact.status !== SymbiosisStatus.ACTIVE) return;

    const population = this.provider.getPopulation();
    const genomeA = population.find(g => g.id === pact.partnerA);
    const genomeB = population.find(g => g.id === pact.partnerB);
    if (!genomeA || !genomeB) {
      this.dissolvePact(pactId, 'Partner no longer exists');
      return;
    }

    for (const [tool, weightA] of Object.entries(genomeA.params.toolWeights)) {
      const weightB = genomeB.params.toolWeights[tool] || 1;
      if (weightA > 1.3 && weightB < 0.8) {
        const boost = (weightA - weightB) * 0.1;
        genomeB.params.toolWeights[tool] = Math.min(2.0, weightB + boost);
        pact.exchanges.push({
          fromId: genomeA.id,
          toId: genomeB.id,
          resource: `tool_boost_${tool}`,
          amount: boost,
          timestamp: Date.now(),
        });
      } else if (weightB > 1.3 && weightA < 0.8) {
        const boost = (weightB - weightA) * 0.1;
        genomeA.params.toolWeights[tool] = Math.min(2.0, weightA + boost);
        pact.exchanges.push({
          fromId: genomeB.id,
          toId: genomeA.id,
          resource: `tool_boost_${tool}`,
          amount: boost,
          timestamp: Date.now(),
        });
      }
    }

    pact.fitness = ((genomeA.fitness || 0) + (genomeB.fitness || 0)) / 2;
    pact.stability = Math.min(1.0, pact.stability + 0.05);
    pact.age++;

    if (pact.age > 10 && pact.synergyScore > 1.5 && pact.stability > 0.8) {
      this.evolveToSuperOrganism(pactId);
    }

    this.detectParasitism(pactId);
  }

  // ─── Évolution en Super-Organisme ──────────────────────

  evolveToSuperOrganism(pactId: string): SuperOrganism | null {
    const pact = this.pacts.get(pactId);
    if (!pact) return null;

    const population = this.provider.getPopulation();
    const genomeA = population.find(g => g.id === pact.partnerA);
    const genomeB = population.find(g => g.id === pact.partnerB);
    if (!genomeA || !genomeB) return null;

    logger.info(`[Symbiotic Protocol] 🧬 SUPER-ORGANISM EVOLUTION: ${pact.partnerA} + ${pact.partnerB} → fusion!`);

    const combinedGenome = genomeA.fuseWith(genomeB);
    combinedGenome.specialties.push('Super-Organism');

    const superOrg: SuperOrganism = {
      id: `super_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`,
      pactId,
      combinedGenome,
      memberIds: [pact.partnerA, pact.partnerB],
      generation: Math.max(genomeA.generation, genomeB.generation) + 1,
      fitness: pact.fitness * pact.synergyScore,
      isViable: true,
      createdAt: Date.now(),
    };

    this.superOrganisms.set(superOrg.id, superOrg);
    this.state.superOrganisms++;
    pact.status = SymbiosisStatus.EVOLVED;

    logger.info(`[Symbiotic Protocol] 🌟 SUPER-ORGANISM created: ${superOrg.id} (fitness: ${superOrg.fitness.toFixed(2)})`);

    // PHASE 2.4 : Émettre un événement pour ImperialCycle
    this.emit('superorganism.created', superOrg);

    return superOrg;
  }

  // ─── Détection de Parasitisme ──────────────────────────

  private detectParasitism(pactId: string): void {
    const pact = this.pacts.get(pactId);
    if (!pact || pact.status !== SymbiosisStatus.ACTIVE) return;

    const aToB = pact.exchanges.filter(e => e.fromId === pact.partnerA).length;
    const bToA = pact.exchanges.filter(e => e.fromId === pact.partnerB).length;

    const totalExchanges = aToB + bToA;
    if (totalExchanges < 5) return;

    const ratio = Math.min(aToB, bToA) / Math.max(aToB, bToA);

    if (ratio < 0.2) {
      this.state.parasitismDetected++;
      logger.warn(`[Symbiotic Protocol] 🦠 PARASITISM DETECTED in pact ${pactId}! A→B: ${aToB}, B→A: ${bToA}`);
      this.dissolvePact(pactId, 'Parasitism detected');
    }
  }

  // ─── Dissolution de Pactes ─────────────────────────────

  private dissolvePact(pactId: string, reason: string): void {
    const pact = this.pacts.get(pactId);
    if (!pact) return;

    const wasActive = pact.status === SymbiosisStatus.ACTIVE;
    pact.status = SymbiosisStatus.DISSOLVED;
    pact.dissolvedAt = Date.now();

    if (wasActive) {
      this.state.activePacts--;
    }

    logger.info(`[Symbiotic Protocol] 💔 Pact DISSOLVED: ${pact.partnerA} ↔ ${pact.partnerB} (reason: ${reason})`);
  }

  // ─── Utilitaires ────────────────────────────────────────

  private determineSymbiosisType(
    genomeA: UnifiedGenome, genomeB: UnifiedGenome,
    complementarity: ComplementarityMap
  ): SymbiosisType {
    const mutualGain = complementarity.aProvidesB.length + complementarity.bProvidesA.length;
    const oneWayGain = Math.max(complementarity.aProvidesB.length, complementarity.bProvidesA.length) -
                       Math.min(complementarity.aProvidesB.length, complementarity.bProvidesA.length);

    if (mutualGain > 4 && oneWayGain < 2) return SymbiosisType.MUTUALISM;
    if (oneWayGain > 3) return SymbiosisType.COMMENSALISM;
    if (complementarity.sharedStrengths.length > 2) return SymbiosisType.CATALYSIS;
    if (genomeA.params.dockerAffinity > 0.8 || genomeB.params.dockerAffinity > 0.8) {
      return SymbiosisType.ENDOSYMBIOSIS;
    }
    return SymbiosisType.MUTUALISM;
  }

  private computeSynergyScore(genomeA: UnifiedGenome, genomeB: UnifiedGenome, complementarity: ComplementarityMap): number {
    const gain = complementarity.aProvidesB.length + complementarity.bProvidesA.length;
    const cost = complementarity.riskAreas.length;
    const shared = complementarity.sharedStrengths.length;
    return (gain * 0.4) + (shared * 0.2) - (cost * 0.3) + 1.0;
  }

  private findActivePact(genomeId: string): SymbioticPact | null {
    for (const pact of this.pacts.values()) {
      if ((pact.partnerA === genomeId || pact.partnerB === genomeId) &&
          (pact.status === SymbiosisStatus.ACTIVE || pact.status === SymbiosisStatus.PROPOSED)) {
        return pact;
      }
    }
    return null;
  }

  // ─── Scan Autonome ─────────────────────────────────────

  scanForSymbioticOpportunities(): SymbioticPact[] {
    const population = this.provider.getPopulation();
    const newPacts: SymbioticPact[] = [];

    for (let i = 0; i < population.length; i++) {
      for (let j = i + 1; j < population.length; j++) {
        if (this.findActivePact(population[i].id)) continue;
        if (this.findActivePact(population[j].id)) continue;

        const pact = this.proposePact(population[i], population[j]);
        if (pact) newPacts.push(pact);
      }
    }

    logger.info(`[Symbiotic Protocol] 🔍 Scan complete. ${newPacts.length} new symbiotic opportunities identified.`);
    return newPacts;
  }

  // ─── Getters ────────────────────────────────────────────

  getState(): SymbioticState {
    return { ...this.state };
  }

  getActivePacts(): SymbioticPact[] {
    return Array.from(this.pacts.values()).filter(p => p.status === SymbiosisStatus.ACTIVE);
  }

  getSuperOrganisms(): SuperOrganism[] {
    return Array.from(this.superOrganisms.values());
  }

  getPact(id: string): SymbioticPact | undefined {
    return this.pacts.get(id);
  }
}
