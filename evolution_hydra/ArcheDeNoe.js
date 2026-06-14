import { Genome, Gene } from './Genome.js';
import logger from '../utils/logger.js';
/**
 * ARCHE DE NOÉ (Gene Bank)
 * Conservation des meilleurs génomes et des gènes "éteints"
 */
export class ArcheDeNoe {
    population = [];
    extinctGenes = new Map(); // Gènes "morts" mais conservés
    capacity;
    constructor(capacity = 1000) {
        this.capacity = capacity;
        logger.info('[Arche de Noé] 🚢 Banque génétique initialisée. Capacité: ' + capacity);
    }
    /**
     * Stocke un génome dans l'arche
     */
    store(genome) {
        // Deep copy simplistic version for memory conservation
        const genomeCopy = new Genome(genome.agentName);
        Object.assign(genomeCopy, JSON.parse(JSON.stringify(genome)));
        this.population.push(genomeCopy);
        // Trier par fitness (en prenant la moyenne des 10 derniers scores)
        this.population.sort((a, b) => this.getAverageFitness(b) - this.getAverageFitness(a));
        if (this.population.length > this.capacity) {
            const eliminated = this.population.pop();
            if (eliminated) {
                // Les gènes des génomes éliminés vont dans "extinct"
                for (const gene of eliminated.g_behavior.slice(0, 10)) { // Conserver un échantillon
                    const key = `${gene.chromosome}_${gene.id}`;
                    if (!this.extinctGenes.has(key)) {
                        this.extinctGenes.set(key, []);
                    }
                    this.extinctGenes.get(key).push(gene);
                }
            }
        }
    }
    getAverageFitness(g) {
        if (g.fitnessHistory.length === 0)
            return 0.5;
        const recent = g.fitnessHistory.slice(-10);
        return recent.reduce((a, b) => a + b, 0) / recent.length;
    }
    /**
     * Retourne le meilleur génome
     */
    getBestParent() {
        return this.population[0];
    }
    /**
     * Ressuscite un gène éteint depuis l'arche
     */
    resurrectGene(chrom, geneId) {
        const key = `${chrom}_${geneId}`;
        const extinctList = this.extinctGenes.get(key);
        if (extinctList && extinctList.length > 0) {
            const randIndex = Math.floor(Math.random() * extinctList.length);
            const resurrected = extinctList[randIndex];
            // Clone it to avoid reference issues
            return new Gene(resurrected.id, resurrected.value, resurrected.chromosome, resurrected.mutable);
        }
        return null;
    }
}
