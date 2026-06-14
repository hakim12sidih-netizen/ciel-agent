import logger from '../utils/logger.js';
import { HardwareMetrics } from '../utils/HardwareMetrics.js';
import type { Genome } from './Genome.js';

/**
 * ═══════════════════════════════════════════════════════════════
 * ENTROPY HARVESTER — Creative Disorder Engine
 * ═══════════════════════════════════════════════════════════════
 *
 * PRINCIPE RÉVOLUTIONNAIRE :
 * L'entropie est l'ennemi de la plupart des systèmes — mais pas
 * de HYDRA. L'EntropyHarvester CAPTURE le désordre naturel du
 * système (CPU fluctuations, erreurs, timing variances) et le
 * TRANSFORME en créativité computationnelle.
 *
 * Fondements théoriques :
 * - Thermodynamique hors équilibre (Prigogine) : les structures
 *   dissipatives UTILISENT le désordre pour s'auto-organiser
 * - Bruit stochastique comme ressource (Stochastic Resonance) :
 *   un certain niveau de bruit AMÉLIORE la détection du signal
 * - Antifragilité (Taleb) : les systèmes qui profitent du désordre
 * - Processus de Poisson comme source de nouveauté
 * - Mutation dirigée par l'entropie : au lieu de combattre
 *   le bruit, l'utiliser comme moteur d'exploration
 *
 * Le Harvester ne produit pas du chaos — il DISTILLE le chaos
 * naturel en VARIATION CRÉATIVE. C'est un alchimiste computationnel
 * qui transforme le plomb du bruit en or de la nouveauté.
 */

// ─── Types de l'Harvester ───────────────────────────────────

export interface EntropySource {
  id: string;
  type: EntropySourceType;
  rawValue: number;
  normalizedValue: number;       // 0-1
  timestamp: number;
  quality: number;               // Qualité de l'entropie (0-1)
}

export enum EntropySourceType {
  CPU_FLUCTUATION = 'CPU_FLUCTUATION',
  MEMORY_VARIANCE = 'MEMORY_VARIANCE',
  EVENT_LOOP_LAG = 'EVENT_LOOP_LAG',
  TIMING_JITTER = 'TIMING_JITTER',
  MUTATION_DRIFT = 'MUTATION_DRIFT',
  NETWORK_LATENCY = 'NETWORK_LATENCY',
  DISK_IO_VARIANCE = 'DISK_IO_VARIANCE',
  THERMAL_NOISE = 'THERMAL_NOISE',
}

export interface HarvestedEntropy {
  id: string;
  sources: EntropySource[];
  compositeValue: number;        // Valeur composite normalisée
  creativePotential: number;     // Potentiel créatif (0-1)
  entropyType: EntropyProfile;
  harvestedAt: number;
  usedFor: string | null;        // Comment cette entropie a été utilisée
}

export enum EntropyProfile {
  CHAOTIC = 'CHAOTIC',           // Entropie pure, non structurée
  STRUCTURED = 'STRUCTURED',     // Entropie avec des patterns sous-jacents
  RESONANT = 'RESONANT',         // Entropie en résonance avec le système
  CATALYTIC = 'CATALYTIC',       // Entropie qui accélère l'évolution
  DORMANT = 'DORMANT',           // Entropie stockée pour usage futur
}

export interface EntropyState {
  totalHarvested: number;
  totalUsed: number;
  harvestRate: number;           // Entropie récoltée par seconde
  creativeYield: number;         // Rendement créatif (0-1)
  dominantProfile: EntropyProfile;
  stochasticResonanceLevel: number; // Niveau de résonance stochastique
  antifragilityIndex: number;    // Indice d'antifragilité du système
}

// ─── Le Récolteur d'Entropie ────────────────────────────────

export class EntropyHarvester {
  private sources: Map<EntropySourceType, EntropySource> = new Map();
  private harvested: HarvestedEntropy[] = [];
  private entropyPool: number[] = [];  // Pool d'entropie brute
  private state: EntropyState;
  private lastHarvestTime: number = Date.now();
  private stochasticResonanceOptimum: number = 0.3; // Niveau optimal de bruit

  constructor() {
    this.state = {
      totalHarvested: 0,
      totalUsed: 0,
      harvestRate: 0,
      creativeYield: 0,
      dominantProfile: EntropyProfile.DORMANT,
      stochasticResonanceLevel: 0,
      antifragilityIndex: 0.5,
    };

    logger.info('[Entropy Harvester] 🌊 Creative Disorder Engine initialized. Chaos is not the enemy — it is the fuel.');
  }

  // ─── Récolte de l'Entropie ─────────────────────────────

  /**
   * Récolte l'entropie naturelle du système.
   * Chaque source de variation est capturée, normalisée, et
   * évaluée pour sa qualité créative.
   */
  harvest(): HarvestedEntropy {
    const now = Date.now();

    // 1. Capturer les sources d'entropie
    const sources: EntropySource[] = [];

    // CPU Fluctuation
    const cpuLoad = HardwareMetrics.getRealCPULoad();
    sources.push(this.createSource(EntropySourceType.CPU_FLUCTUATION, cpuLoad));

    // Memory Variance
    const memUsage = HardwareMetrics.getRealMemoryUsage();
    sources.push(this.createSource(EntropySourceType.MEMORY_VARIANCE, memUsage));

    // Event Loop Lag
    const lag = HardwareMetrics.getEventLoopLag();
    sources.push(this.createSource(EntropySourceType.EVENT_LOOP_LAG, lag / 100)); // Normaliser

    // Timing Jitter
    const jitter = Math.abs((now - this.lastHarvestTime) - 1000) / 1000; // Variation par rapport à 1s
    sources.push(this.createSource(EntropySourceType.TIMING_JITTER, Math.min(1, jitter)));

    // Thermal Noise (simulation basée sur les fluctuations CPU)
    const thermalNoise = Math.abs(cpuLoad - 0.5) * 2; // Plus c'est loin de 0.5, plus il y a de chaleur
    sources.push(this.createSource(EntropySourceType.THERMAL_NOISE, thermalNoise));

    this.lastHarvestTime = now;

    // 2. Calculer la valeur composite
    const compositeValue = this.computeCompositeEntropy(sources);

    // 3. Déterminer le profil d'entropie
    const entropyType = this.classifyEntropy(sources, compositeValue);

    // 4. Calculer le potentiel créatif
    const creativePotential = this.computeCreativePotential(sources, entropyType);

    // 5. Créer l'entrée récoltée
    const harvested: HarvestedEntropy = {
      id: `entropy_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`,
      sources,
      compositeValue,
      creativePotential,
      entropyType,
      harvestedAt: now,
      usedFor: null,
    };

    this.harvested.push(harvested);
    this.entropyPool.push(compositeValue);
    this.state.totalHarvested++;

    // Garder le pool à une taille raisonnable
    if (this.entropyPool.length > 1000) {
      this.entropyPool = this.entropyPool.slice(-500);
    }

    // Mettre à jour les stats
    this.updateStats(harvested);

    logger.debug(`[Entropy Harvester] 🌊 Harvested entropy: ${compositeValue.toFixed(3)} (type: ${entropyType}, creative: ${creativePotential.toFixed(3)})`);

    return harvested;
  }

  // ─── Utilisation de l'Entropie ─────────────────────────

  /**
   * Utilise l'entropie récoltée pour alimenter un processus créatif.
   * L'entropie est dirigée vers là où elle sera la plus productive.
   */
  useEntropy(purpose: string, requiredAmount: number = 0.3): HarvestedEntropy | null {
    // Trouver l'entrée récoltée la plus appropriée
    let bestMatch: HarvestedEntropy | null = null;
    let bestScore = 0;

    for (const h of this.harvested) {
      if (h.usedFor !== null) continue; // Déjà utilisée

      // Score basé sur la proximité du potentiel créatif avec le besoin
      const match = 1 - Math.abs(h.creativePotential - requiredAmount);

      // Bonus pour les profils catalytiques et résonants
      const profileBonus = h.entropyType === EntropyProfile.CATALYTIC ? 0.3 :
                           h.entropyType === EntropyProfile.RESONANT ? 0.2 : 0;

      const score = match + profileBonus;

      if (score > bestScore) {
        bestScore = score;
        bestMatch = h;
      }
    }

    if (bestMatch) {
      bestMatch.usedFor = purpose;
      this.state.totalUsed++;

      logger.debug(`[Entropy Harvester] ⚡ Entropy USED for: ${purpose} (creative: ${bestMatch.creativePotential.toFixed(3)})`);
    }

    return bestMatch;
  }

  /**
   * Génère une mutation créative basée sur l'entropie récoltée.
   * Au lieu de mutations aléatoires pures, les mutations sont
   * GUIDÉES par l'entropie structurée.
   */
  generateCreativeMutation(genome: Genome): {
    targetParam: string;
    delta: number;
    rationale: string;
  } | null {
    const entropy = this.useEntropy(`mutation_${genome.id}`, 0.5);
    if (!entropy) return null;

    // Choisir le paramètre à muter basé sur le profil d'entropie
    let targetParam: string;
    let delta: number;
    let rationale: string;

    switch (entropy.entropyType) {
      case EntropyProfile.CHAOTIC:
        // L'entropie chaotique pousse vers des mutations exploratoires
        targetParam = 'temperature';
        delta = entropy.compositeValue * 0.5 - 0.25; // ±0.25
        rationale = `Chaotic entropy surge driving temperature exploration (Δ=${delta.toFixed(3)})`;
        break;

      case EntropyProfile.STRUCTURED:
        // L'entropie structurée guide vers des mutations de spécialisation
        targetParam = 'promptMutation';
        const traits = [
          'Be highly analytical and concise.',
          'Think step-by-step and write pseudocode before coding.',
          'Propose radically different alternative solutions.',
        ];
        delta = 0; // Pour promptMutation, delta n'est pas utilisé
        rationale = traits[Math.floor(entropy.compositeValue * traits.length)];
        targetParam = 'promptMutation';
        break;

      case EntropyProfile.RESONANT:
        // L'entropie résonante amplifie les forces existantes
        const tools = Object.keys(genome.params.toolWeights);
        targetParam = `tool_${tools[Math.floor(entropy.compositeValue * tools.length)]}`;
        delta = entropy.creativePotential * 0.3; // Amplification positive
        rationale = `Resonant entropy amplifying existing tool affinity (${targetParam})`;
        break;

      case EntropyProfile.CATALYTIC:
        // L'entropie catalytique provoque des sauts qualitatifs
        targetParam = 'polyglotDepth';
        delta = entropy.compositeValue * 0.4; // Saut significatif
        rationale = `Catalytic entropy triggering qualitative leap in polyglot capability`;
        break;

      default:
        targetParam = 'episodicRetention';
        delta = entropy.compositeValue * 0.2 - 0.1;
        rationale = `Dormant entropy gently adjusting memory retention`;
    }

    return { targetParam, delta, rationale };
  }

  // ─── Résonance Stochastique ────────────────────────────

  /**
   * La résonance stochastique se produit quand un niveau OPTIMAL
   * de bruit AMÉLIORE la performance du système.
   * L'Harvester surveille ce niveau et ajuste l'apport en bruit.
   */
  computeStochasticResonance(systemPerformance: number): number {
    // La performance du système en fonction du bruit suit une courbe en U inversé
    // Il y a un optimum de bruit où la performance est maximale
    const noiseLevel = this.state.harvestRate;
    const optimum = this.stochasticResonanceOptimum;

    // La résonance est maximale quand le bruit est proche de l'optimum
    const deviation = Math.abs(noiseLevel - optimum) / optimum;
    const resonance = Math.exp(-deviation * deviation * 2); // Courbe gaussienne

    this.state.stochasticResonanceLevel = resonance;

    // Ajuster l'optimum basé sur la performance observée
    if (systemPerformance > 0.7 && resonance > 0.5) {
      // Bonne performance avec bonne résonance → l'optimum est correct
    } else if (systemPerformance < 0.3 && noiseLevel > optimum) {
      // Mauvaise performance avec trop de bruit → réduire l'optimum
      this.stochasticResonanceOptimum *= 0.95;
    } else if (systemPerformance < 0.3 && noiseLevel < optimum) {
      // Mauvaise performance avec trop peu de bruit → augmenter l'optimum
      this.stochasticResonanceOptimum = Math.min(0.8, this.stochasticResonanceOptimum * 1.05);
    }

    return resonance;
  }

  // ─── Antifragilité ─────────────────────────────────────

  /**
   * Mesure l'antifragilité du système : un système antifragile
   * PROFITE du désordre (il s'améliore quand il est stressé).
   */
  computeAntifragilityIndex(recentPerformanceHistory: number[]): number {
    if (recentPerformanceHistory.length < 5) return 0.5;

    // Comparer la performance après les périodes de haute entropie
    // vs après les périodes de basse entropie
    const half = Math.floor(recentPerformanceHistory.length / 2);
    const firstHalf = recentPerformanceHistory.slice(0, half);
    const secondHalf = recentPerformanceHistory.slice(half);

    const avgFirst = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const avgSecond = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;

    // Si le système s'améliore avec le temps (même avec le stress), il est antifragile
    const improvement = avgSecond - avgFirst;

    // Si le système se dégrade avec le stress, il est fragile
    this.state.antifragilityIndex = Math.tanh(improvement * 5 + 0.5);

    if (this.state.antifragilityIndex > 0.7) {
      logger.info(`[Entropy Harvester] 💪 ANTIFRAGILE: System improves under stress (index: ${this.state.antifragilityIndex.toFixed(3)})`);
    } else if (this.state.antifragilityIndex < 0.3) {
      logger.warn(`[Entropy Harvester] ⚠️ FRAGILE: System degrades under stress (index: ${this.state.antifragilityIndex.toFixed(3)})`);
    }

    return this.state.antifragilityIndex;
  }

  // ─── Utilitaires ────────────────────────────────────────

  private createSource(type: EntropySourceType, rawValue: number): EntropySource {
    return {
      id: `src_${type}_${Date.now()}`,
      type,
      rawValue,
      normalizedValue: Math.max(0, Math.min(1, rawValue)),
      timestamp: Date.now(),
      quality: this.assessSourceQuality(type, rawValue),
    };
  }

  private assessSourceQuality(type: EntropySourceType, value: number): number {
    // La qualité dépend de la source et de la valeur
    // Les valeurs extrêmes (proches de 0 ou 1) ont souvent une meilleure qualité
    // car elles sont moins prévisibles
    switch (type) {
      case EntropySourceType.CPU_FLUCTUATION:
        return value > 0.3 && value < 0.9 ? 0.8 : 0.4; // Zone productive
      case EntropySourceType.THERMAL_NOISE:
        return value > 0.5 ? 0.9 : 0.3; // Plus de chaleur = plus d'entropie
      case EntropySourceType.TIMING_JITTER:
        return value > 0.1 ? 0.7 : 0.2; // Le jitter est une bonne source
      default:
        return 0.5;
    }
  }

  private computeCompositeEntropy(sources: EntropySource[]): number {
    // Moyenne pondérée par la qualité
    let totalWeight = 0;
    let weightedSum = 0;

    for (const source of sources) {
      weightedSum += source.normalizedValue * source.quality;
      totalWeight += source.quality;
    }

    return totalWeight > 0 ? weightedSum / totalWeight : 0;
  }

  private classifyEntropy(sources: EntropySource[], composite: number): EntropyProfile {
    // Variance entre les sources
    const values = sources.map(s => s.normalizedValue);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const variance = values.reduce((acc, v) => acc + Math.pow(v - avg, 2), 0) / values.length;

    // Haute variance = chaotique
    // Basse variance = structuré
    // Variance modérée avec haute qualité = résonant
    // Composite élevé = catalytique

    const avgQuality = sources.reduce((acc, s) => acc + s.quality, 0) / sources.length;

    if (composite > 0.7 && avgQuality > 0.6) return EntropyProfile.CATALYTIC;
    if (variance < 0.05 && avgQuality > 0.5) return EntropyProfile.RESONANT;
    if (variance > 0.15) return EntropyProfile.CHAOTIC;
    if (variance < 0.05) return EntropyProfile.STRUCTURED;
    return EntropyProfile.DORMANT;
  }

  private computeCreativePotential(sources: EntropySource[], profile: EntropyProfile): number {
    // Le potentiel créatif dépend du profil et de la qualité
    const profileMultiplier: Record<EntropyProfile, number> = {
      [EntropyProfile.CATALYTIC]: 1.0,
      [EntropyProfile.RESONANT]: 0.8,
      [EntropyProfile.CHAOTIC]: 0.6,
      [EntropyProfile.STRUCTURED]: 0.5,
      [EntropyProfile.DORMANT]: 0.2,
    };

    const avgQuality = sources.reduce((acc, s) => acc + s.quality, 0) / sources.length;
    const composite = this.computeCompositeEntropy(sources);

    return Math.min(1.0, composite * avgQuality * (profileMultiplier[profile] || 0.5));
  }

  private updateStats(latestHarvest: HarvestedEntropy): void {
    // Taux de récolte
    const timeSinceLastHarvest = (Date.now() - this.lastHarvestTime) / 1000;
    this.state.harvestRate = timeSinceLastHarvest > 0
      ? 1 / timeSinceLastHarvest
      : 0;

    // Rendement créatif
    const usedEntries = this.harvested.filter(h => h.usedFor !== null);
    this.state.creativeYield = this.state.totalHarvested > 0
      ? usedEntries.length / this.state.totalHarvested
      : 0;

    // Profil dominant
    const profileCounts: Record<EntropyProfile, number> = {
      [EntropyProfile.CHAOTIC]: 0,
      [EntropyProfile.STRUCTURED]: 0,
      [EntropyProfile.RESONANT]: 0,
      [EntropyProfile.CATALYTIC]: 0,
      [EntropyProfile.DORMANT]: 0,
    };

    for (const h of this.harvested.slice(-100)) {
      profileCounts[h.entropyType]++;
    }

    let maxCount = 0;
    for (const [profile, count] of Object.entries(profileCounts)) {
      if (count > maxCount) {
        maxCount = count;
        this.state.dominantProfile = profile as EntropyProfile;
      }
    }
  }

  // ─── Getters ────────────────────────────────────────────

  getState(): EntropyState {
    return { ...this.state };
  }

  getEntropyPool(): number[] {
    return [...this.entropyPool];
  }

  getRecentHarvests(limit: number = 50): HarvestedEntropy[] {
    return this.harvested.slice(-limit);
  }
}
