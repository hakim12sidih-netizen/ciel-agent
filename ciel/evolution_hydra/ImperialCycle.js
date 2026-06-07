/**
 * ═══════════════════════════════════════════════════════════════
 * IMPERIAL-CYCLE v2 — Sélection darwinienne réelle
 * ═══════════════════════════════════════════════════════════════
 *
 * PHASE 2 : Refactorisé pour :
 * 1. Stocker de vrais `UnifiedGenome` (au lieu de strings `agent_X_Y`)
 * 2. Évaluer la fitness via `DefaultFitnessEvaluator` + `HydraContext`
 * 3. Écouter les événements `superorganism.created` de SymbioticProtocol
 * 4. Sélectionner vraiment les 10 meilleurs sur 100 (au lieu de slice(0,10))
 * 5. Détecter les factions émergentes par clustering de spécialités
 *    (au lieu de hardcoder 2 clusters)
 * 6. Implémenter `IGenomeProvider` pour être utilisé par SymbioticProtocol
 */
import { EventEmitter } from 'events';
import { TitanEcosystem } from './TitanEcosystem.js';
import { SymbioticProtocol } from './SymbioticProtocol.js';
import { UnifiedGenome } from './UnifiedGenome.js';
import { DefaultFitnessEvaluator } from './FitnessEvaluator.js';
import logger from '../utils/logger.js';
/**
 * IMPERIAL-CYCLE — Gère le destin de 100 agents par génération.
 * Implémente `IGenomeProvider` pour être consommé par SymbioticProtocol.
 */
export class ImperialCycle extends EventEmitter {
    hydra;
    genetic;
    population = [];
    generation = 0;
    ecosystem;
    evaluator;
    symbiotic;
    lastContext;
    elites = [];
    superOrganismsAdded = 0;
    populationSize;
    eliteSize;
    constructor(hydra, genetic, options = {}) {
        super();
        this.hydra = hydra;
        this.genetic = genetic;
        this.ecosystem = options.ecosystem ?? new TitanEcosystem();
        this.evaluator = options.evaluator ?? new DefaultFitnessEvaluator();
        this.symbiotic = options.symbiotic ?? new SymbioticProtocol(this);
        this.populationSize = options.populationSize ?? 100;
        this.eliteSize = options.eliteSize ?? 10;
        // PHASE 2.4 : Écouter les super-organismes créés par SymbioticProtocol
        this.symbiotic.on('superorganism.created', (org) => {
            this.onSuperOrganismCreated(org);
        });
    }
    // ──────────────────────────────────────────────────────────
    // IGenomeProvider — expose la population à SymbioticProtocol
    // ──────────────────────────────────────────────────────────
    getPopulation() {
        return [...this.population];
    }
    // ──────────────────────────────────────────────────────────
    // Configuration du contexte d'évaluation
    // ──────────────────────────────────────────────────────────
    /**
     * Met à jour le contexte Hydra pour la prochaine évaluation.
     * Typiquement appelé après chaque session HydraCore.
     */
    setContext(context) {
        this.lastContext = context;
    }
    // ──────────────────────────────────────────────────────────
    // Cycle de vie principal
    // ──────────────────────────────────────────────────────────
    async runGeneration(context) {
        this.generation++;
        if (context)
            this.lastContext = context;
        this.superOrganismsAdded = 0;
        logger.info(`[ARENA] 🏛️ Lancement de la Génération #${this.generation}`);
        // 1. PHASE DE GENESIS : Création de vrais UnifiedGenome
        this.spawnPopulation(this.populationSize);
        // 2. PHASE DE LA SANGLANTE : Évaluation et Sélection RÉELLE 10/90
        const survivors = this.evaluateAndSelect(this.eliteSize);
        const dead = this.population.filter(g => !survivors.includes(g));
        const bestFit = survivors[0]?.fitnessScore() ?? 0;
        const medianFit = this.computeMedianFitness();
        logger.info(`[ARENA] ⚔️ La Sanglante est terminée. ${survivors.length} survivants, ${dead.length} morts.`);
        logger.info(`[ARENA]    Best fitness: ${bestFit.toFixed(3)}, median: ${medianFit.toFixed(3)}`);
        // 3. PHASE DE FUSION (Testaments) : vrais échanges génétiques
        for (const survivor of survivors) {
            const victims = this.pickRandom(dead, 7);
            for (const victim of victims) {
                await this.genetic.absorbInto(survivor, victim);
            }
        }
        // 4. ÉLECTION DES CHEFS + DÉTECTION DES FACTIONS ÉMERGENTES
        const clusters = this.detectEmergentFactions(survivors);
        for (const [factionName, members] of Object.entries(clusters)) {
            logger.info(`[ARENA] 🧬 Faction "${factionName}" : ${members.length} membres`);
            if (members.length >= 2) {
                const chief = members[0];
                const partner = members[1];
                this.genetic.generateHeirsFrom(chief, partner);
            }
        }
        this.elites = survivors;
        // PHASE 2.5 : Régénérer la population à partir des élites
        // Les 10 élites survivent, les 90 autres places sont remplies par
        // crossover de paires d'élites (sélection sexuelle darwinienne).
        const newPopulation = [...survivors];
        const slots = this.populationSize - survivors.length;
        for (let i = 0; i < slots; i++) {
            const p1 = this.pickRandom(survivors, 1)[0];
            const p2 = this.pickRandom(survivors, 1)[0];
            const child = p1.crossover(p2);
            child.agentName = `agent_g${this.generation}_offspring_${i}`;
            child.mutate(0.15);
            newPopulation.push(child);
        }
        this.population = newPopulation;
        const result = {
            generation: this.generation,
            survivors,
            dead,
            clusters,
            bestFitness: bestFit,
            medianFitness: medianFit,
            superOrganismsAdded: this.superOrganismsAdded,
        };
        this.emit('generation.complete', result);
        return result;
    }
    // ──────────────────────────────────────────────────────────
    // PHASE 1 : Genesis
    // ──────────────────────────────────────────────────────────
    spawnPopulation(count) {
        logger.debug(`[ARENA] 🧬 Génération de ${count} embryons...`);
        const newGenomes = [];
        for (let i = 0; i < count; i++) {
            // S'il y a des élites de la génération précédente, on les utilise comme parents
            const parent = this.elites.length > 0
                ? this.elites[Math.floor(Math.random() * this.elites.length)]
                : null;
            let child;
            if (parent) {
                // Mutation du parent pour créer un enfant
                child = parent.clone();
                child.agentName = `agent_g${this.generation}_${i}`;
                child.mutate(0.1);
            }
            else {
                // Première génération : génome neuf
                child = new UnifiedGenome({
                    agentName: `agent_g${this.generation}_${i}`,
                    generation: this.generation,
                });
            }
            newGenomes.push(child);
        }
        this.population = newGenomes;
    }
    // ──────────────────────────────────────────────────────────
    // PHASE 2 : La Sanglante (sélection RÉELLE)
    // ──────────────────────────────────────────────────────────
    evaluateAndSelect(count) {
        // Évaluer chaque génome
        const scored = this.population.map(g => ({
            genome: g,
            fitness: this.evaluator.evaluate(g, this.lastContext),
        }));
        // Trier par fitness décroissante
        scored.sort((a, b) => b.fitness - a.fitness);
        // Élitisme : garder le top `count`
        const elites = scored.slice(0, count);
        return elites.map(s => s.genome);
    }
    computeMedianFitness() {
        if (this.population.length === 0)
            return 0;
        const sorted = [...this.population]
            .map(g => g.fitnessScore())
            .sort((a, b) => a - b);
        const mid = Math.floor(sorted.length / 2);
        return sorted[mid] ?? 0;
    }
    // ──────────────────────────────────────────────────────────
    // PHASE 4 : Détection des factions émergentes (clustering)
    // ──────────────────────────────────────────────────────────
    detectEmergentFactions(survivors) {
        // Clustering par spécialité partagée (clé = première spécialité)
        const clusters = {};
        for (const g of survivors) {
            const key = g.specialties[0] ?? 'Alpha';
            if (!clusters[key])
                clusters[key] = [];
            clusters[key].push(g);
        }
        return clusters;
    }
    // ──────────────────────────────────────────────────────────
    // PHASE 2.4 : Intégration des super-organismes
    // ──────────────────────────────────────────────────────────
    onSuperOrganismCreated(org) {
        this.population.push(org.combinedGenome);
        this.superOrganismsAdded++;
        logger.info(`[ARENA] 🧬 Super-organism ajouté à la population : ${org.combinedGenome.id} (fitness: ${org.fitness.toFixed(3)})`);
        this.emit('superorganism.added', org);
    }
    // ──────────────────────────────────────────────────────────
    // Helpers
    // ──────────────────────────────────────────────────────────
    pickRandom(array, n) {
        // Copie pour ne pas muter l'input
        const copy = [...array];
        const result = [];
        for (let i = 0; i < Math.min(n, copy.length); i++) {
            const idx = Math.floor(Math.random() * copy.length);
            result.push(copy.splice(idx, 1)[0]);
        }
        return result;
    }
    getElites() {
        return [...this.elites];
    }
    getCurrentGeneration() {
        return this.generation;
    }
}
