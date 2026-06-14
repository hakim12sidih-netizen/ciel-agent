import { Genome } from './Genome.js';
import { Faction } from './Faction.js';
import logger from '../utils/logger.js';

/**
 * GENETIC ALGORITHM — The Evolutionary substrate of HYDRA.
 * It manages the population of clones and their mutations.
 */
export class GeneticAlgorithm {
  public population: Genome[] = [];
  public factions: Faction[] = [];
  public generation: number = 0;

  constructor(initialSize: number = 5) {
    logger.info(`[Genetic Algorithm] 🧬 Initializing evolution with ${initialSize} seeds.`);
    for (let i = 0; i < initialSize; i++) {
      const genome = new Genome(0);
      this.population.push(genome);
      this.factions.push(new Faction(genome));
    }
  }

  public getUnevaluatedGenome(): Genome | null {
    return this.population.find(g => g.fitness === 0) || null;
  }

  public recordFitness(genomeId: string, sourceId: string, score: number): void {
    const genome = this.population.find(g => g.id === genomeId);
    if (genome) {
      genome.fitness = (genome.fitness + score) / 2;
      logger.debug(`[Genetic Algorithm] 🧬 Genome ${genomeId} fitness updated to ${genome.fitness.toFixed(4)} by ${sourceId}`);
    }
  }

  public evolve(): void {
    this.generation++;
    logger.info(`[Genetic Algorithm] 🚀 Starting Evolution Cycle - Generation ${this.generation}`);
    
    // 1. Sort by fitness (DESC)
    const sortedPopulation = [...this.population].sort((a, b) => b.fitness - a.fitness);
    
    // 2. Elitism: Keep the top 2 Alphas unchanged
    const newPopulation: Genome[] = [sortedPopulation[0], sortedPopulation[1]];
    
    // 3. Selective Breeding (Tournament Selection & Crossover)
    while (newPopulation.length < this.population.length) {
      const parent1 = this.tournamentSelection(sortedPopulation);
      const parent2 = this.tournamentSelection(sortedPopulation);
      
      let offspring: Genome;
      const roll = Math.random();
      
      if (roll < 0.4) {
        // Crossover (Exploitation)
        offspring = parent1.crossover(parent2);
      } else if (roll < 0.7) {
        // Fusion (Synergy)
        offspring = parent1.fuseWith(parent2);
      } else {
        // Mutation level-up of a parent
        offspring = new Genome(this.generation, { ...parent1.params });
        offspring.mutate(0.2);
      }
      
      // Post-birth mutation
      if (Math.random() < 0.1) offspring.mutate();
      
      newPopulation.push(offspring);
    }
    
    this.population = newPopulation;
  }

  private tournamentSelection(population: Genome[], size: number = 3): Genome {
    const participants: Genome[] = [];
    for (let i = 0; i < size; i++) {
      participants.push(population[Math.floor(Math.random() * population.length)]);
    }
    return participants.sort((a, b) => b.fitness - a.fitness)[0];
  }

  public getPopulation(): Genome[] {
    return this.population;
  }

  public getBestGenome(): Genome {
    return [...this.population].sort((a, b) => b.fitness - a.fitness)[0];
  }

  /**
   * Returns the top N genomes to represent the Council.
   * Prioritizes fitness but ensures some diversity if possible.
   */
  public getAlphaGenomes(count: number = 5): Genome[] {
    const sorted = [...this.population].sort((a, b) => b.fitness - a.fitness);
    
    // If we have less than count, return all
    if (sorted.length <= count) return sorted;

    // To ensure diversity, we take the best, then try to find high-fitness genomes 
    // from different factions if they exist
    const selected: Genome[] = [];
    const factionsSeen = new Set<string>();

    for (const genome of sorted) {
      if (selected.length >= count) break;
      
      const factionId = genome.factionId || 'none';
      if (!factionsSeen.has(factionId)) {
        selected.push(genome);
        factionsSeen.add(factionId);
      }
    }

    // If we still need more, fill with remaining best
    for (const genome of sorted) {
      if (selected.length >= count) break;
      if (!selected.includes(genome)) {
        selected.push(genome);
      }
    }

    return selected;
  }
}