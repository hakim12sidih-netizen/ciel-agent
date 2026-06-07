import { ChromosomeType } from './TitanGenome.js';
import { ArcheDeNoe } from './ArcheDeNoe.js';
import logger from '../utils/logger.js';

export type MutationStrategy = 
  | 'gaussian'     // TYPE 1: Mutation Gaussienne Structurée
  | 'epigenetic'   // TYPE 2: Mutation Épigénétique
  | 'transposon'   // TYPE 3: Mutation Transposon (saut de gène)
  | 'bricolage'    // TYPE 4: Bricolage Génétique (arche)
  | 'sacrifice';   // TYPE 5: Mutation Auto-destructrice (altruisme)

interface EditableGene {
  id: number;
  value: number;
  chromosome: ChromosomeType | string;
  mutable: boolean;
  h3k4me3: number;
  h3k27me3: number;
  dna_methylation: number;
  express(): number;
}

interface EditableGenome {
  agentName: string;
  generation: number;
  fitnessHistory: number[];
  g_struct: EditableGene[];
  g_behavior: EditableGene[];
  g_epi: EditableGene[];
  g_meta: EditableGene[];
  clone(): EditableGenome;
  getPhenotype(): Record<string, number>;
}

export class CRISPR_Titan {
  private geneBank: ArcheDeNoe;
  private successRate: number = 0.5;

  constructor(geneBank: ArcheDeNoe) {
    this.geneBank = geneBank;
    logger.info('[CRISPR-Titan] 🧬 Moteur d\'édition génique dirigée (5 opérateurs) initialisé.');
  }

  /**
   * Édite un gène spécifique d'un génome selon une stratégie
   * Stratégies valides : gaussian, epigenetic, transposon, bricolage, sacrifice
   * Le clone est d'abord testé (simulateClone), puis appliqué si la fitness augmente.
   */
  public async edit(genome: EditableGenome, targetGeneId: number, chrom: ChromosomeType, strategy: MutationStrategy): Promise<EditableGenome> {
    logger.debug(`[CRISPR-Titan] Édition du gène ${targetGeneId} sur ${chrom} via ${strategy}`);

    // Clone pour tester l'édition
    const clone = genome.clone();
    let newValue = this.getGeneValue(genome, targetGeneId, chrom);

    switch (strategy) {
      case 'gaussian':
        newValue = this.gaussianMutation(newValue);
        break;
      case 'transposon':
        newValue = this.transposonMutation(genome) ?? newValue;
        break;
      case 'bricolage':
        const extinctGene = this.geneBank.resurrectGene(chrom, targetGeneId);
        if (extinctGene) newValue = extinctGene.value;
        break;
      case 'sacrifice':
        newValue = 0.0; // Désactivation forcée (altruisme)
        break;
      case 'epigenetic':
        // C'est juste un marquage, pas de changement de valeur de base
        break;
    }

    if (strategy !== 'epigenetic') {
      this.applyMutation(clone, targetGeneId, chrom, newValue);
    }
    
    // Test simulation (simplifié)
    const cloneFitness = await this.simulateClone(clone);
    const originalFitness = genome.fitnessHistory.length > 0 ? genome.fitnessHistory[genome.fitnessHistory.length - 1] : 0.5;

    // Décision
    if (cloneFitness > originalFitness || strategy === 'sacrifice') {
      // Succès: appliquer au vrai génome
      this.applyMutation(genome, targetGeneId, chrom, newValue);
      this.epigeneticMark(genome, targetGeneId, chrom, 'activated');
      this.successRate = 0.9 * this.successRate + 0.1;
      return genome;
    } else {
      // Échec: rollback et répression
      this.epigeneticMark(genome, targetGeneId, chrom, 'repressed');
      this.successRate = 0.9 * this.successRate;
      return genome;
    }
  }

  private gaussianMutation(current: number, stdDev = 0.1): number {
    const noise = (Math.random() - 0.5) * (stdDev / 0.1);
    return Math.max(0, Math.min(1, current + noise));
  }

  private transposonMutation(genome: EditableGenome): number | null {
    const chroms = [ChromosomeType.STRUCT, ChromosomeType.BEHAVIOR, ChromosomeType.EPI, ChromosomeType.META];
    const sourceChrom = chroms[Math.floor(Math.random() * chroms.length)];
    const sourceGeneId = Math.floor(Math.random() * 100); 
    return this.getGeneValue(genome, sourceGeneId, sourceChrom);
  }

  private applyMutation(genome: EditableGenome, target: number, chrom: ChromosomeType, value: number) {
    const genes = this.getChromosome(genome, chrom);
    if (genes[target] && genes[target].mutable) {
      genes[target].value = value;
    }
  }

  public epigeneticMark(genome: EditableGenome, target: number, chrom: ChromosomeType, markType: 'activated' | 'repressed' | 'trial') {
    const genes = this.getChromosome(genome, chrom);
    if (!genes[target]) return;

    if (markType === 'activated') {
      genes[target].h3k4me3 = 0.9;
      genes[target].h3k27me3 = 0.1;
    } else if (markType === 'repressed') {
      genes[target].h3k4me3 = 0.1;
      genes[target].h3k27me3 = 0.9;
    } else if (markType === 'trial') {
      genes[target].h3k4me3 = 0.5;
      genes[target].h3k27me3 = 0.5;
    }
  }

  private getChromosome(genome: EditableGenome, chrom: ChromosomeType): EditableGene[] {
    switch (chrom) {
      case ChromosomeType.STRUCT: return genome.g_struct;
      case ChromosomeType.BEHAVIOR: return genome.g_behavior;
      case ChromosomeType.EPI: return genome.g_epi;
      case ChromosomeType.META: return genome.g_meta;
    }
  }

  private getGeneValue(genome: EditableGenome, target: number, chrom: ChromosomeType): number {
    const genes = this.getChromosome(genome, chrom);
    return genes[target] ? genes[target].value : 0.5;
  }

  public async simulateClone(clone: EditableGenome): Promise<number> {
    // P1-A: Calcul DÉTERMINISTE basé sur le phénotype réel du clone
    const phenotype = clone.getPhenotype();

    // Score architectural : des couches dans la plage optimale (24-72) donnent plus de points
    const layerScore = phenotype['num_layers'] >= 24 && phenotype['num_layers'] <= 72 ? 1.0 : 0.5;

    // Score comportemental : exploration + créativité bien équilibrées
    const explorationScore = 1.0 - Math.abs(phenotype['exploration_rate'] - 0.6);
    const creativityScore  = 1.0 - Math.abs(phenotype['creativity_index']  - 0.5);

    // Score méta-génomique : learning_rate dans une plage saine
    const lr = phenotype['learning_rate'];
    const lrScore = lr >= 1e-4 && lr <= 1e-2 ? 1.0 : lr >= 1e-5 ? 0.6 : 0.2;

    // Score épigénétique global : moyenne des expressions actives des gènes struct
    let epiSum = 0;
    const sample = Math.min(50, clone.g_struct.length);
    for (let i = 0; i < sample; i++) epiSum += clone.g_struct[i].express();
    const epiScore = epiSum / sample;

    // Historique de fitness du clone (s'il en a un)
    const historyBase = clone.fitnessHistory.length > 0
      ? clone.fitnessHistory[clone.fitnessHistory.length - 1]
      : 0.5;

    // Pondération finale (sans aucun aléatoire)
    const fitness =
      historyBase   * 0.30 +
      layerScore    * 0.20 +
      explorationScore * 0.15 +
      creativityScore  * 0.15 +
      lrScore       * 0.10 +
      epiScore      * 0.10;

    return Math.max(0, Math.min(1, fitness));
  }
}
