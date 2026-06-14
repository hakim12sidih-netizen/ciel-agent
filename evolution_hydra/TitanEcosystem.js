import logger from '../utils/logger.js';
import { TitanGenome, ChromosomeType } from './TitanGenome.js';
import { ArcheDeNoe } from './ArcheDeNoe.js';
import { CRISPR_Titan } from './CRISPR_Titan.js';
import { TitanRL } from './TitanRL.js';
export class EvolutionaryAgent {
    name;
    genome;
    rl;
    crispr;
    arche;
    dreamQueue = [];
    currentFitness = 0.5;
    constructor(name, arche, crispr) {
        this.name = name;
        this.genome = new TitanGenome(name, true);
        this.arche = arche;
        this.crispr = crispr;
        this.rl = new TitanRL();
    }
    async executeTask(taskResult) {
        // Le vrai système utiliserait H-RL pour choisir l'action
        const fitness = await this.rl.learn(this.genome, taskResult);
        this.currentFitness = fitness;
        // Check pour évolution (arbitraire ici)
        if (this.genome.fitnessHistory.length % 50 === 0) {
            await this.evolve();
        }
    }
    async evolve() {
        const history = this.genome.fitnessHistory;
        const recentFitness = history.slice(-50).reduce((a, b) => a + b, 0) / 50;
        if (history.length > 100) {
            const oldFitness = history.slice(-100, -50).reduce((a, b) => a + b, 0) / 50;
            if (recentFitness < oldFitness * 1.01) {
                // Stagnation
                await this.aggressiveMutation();
            }
        }
        // Store dans l'Arche
        // (Dans la vraie implémentation, on l'ajoute à l'arche de Noé)
        this.genome.generation++;
    }
    async aggressiveMutation() {
        logger.warn(`🔥 ${this.name}: STAGNATION DÉTECTÉE → MUTATION AGRESSIVE`);
        for (let i = 0; i < 10; i++) {
            const target = Math.floor(Math.random() * 100);
            await this.crispr.edit(this.genome, target, ChromosomeType.BEHAVIOR, 'transposon');
        }
    }
}
export class TitanEcosystem {
    agents = new Map();
    generation = 0;
    extinctionEvents = 0;
    symbiosisCount = 0;
    arche;
    crispr;
    olympians = [
        'ZEUS', 'HYDRA', 'ATHENA', 'HEPHAISTOS', 'DIONYSOS',
        'HADES', 'ARTEMIS', 'POSEIDON', 'APOLLON', 'TETHYS',
        'TARTARE', 'NEMESIS', 'PROMETHEE', 'ERIS', 'MORPHEE',
        'CHRONOS', 'PSYCHE', 'THANATOS', 'HECATE', 'URANUS'
    ];
    constructor() {
        this.arche = new ArcheDeNoe();
        this.crispr = new CRISPR_Titan(this.arche);
        // Initialisation
        for (const name of this.olympians) {
            this.agents.set(name, new EvolutionaryAgent(name, this.arche, this.crispr));
        }
        logger.info(`[Titan-Evo] 🌱 Écosystème créé avec ${this.agents.size} agents (Panthéon v2).`);
    }
    async runEvolutionCycle() {
        logger.info(`\n🧬 CYCLE D'ÉVOLUTION #${this.generation} INITÉ...`);
        const fitnessScores = new Map();
        // 1. ÉVALUATION
        for (const [name, agent] of this.agents.entries()) {
            const history = agent.genome.fitnessHistory;
            const fitness = history.length ? history.slice(-100).reduce((a, b) => a + b, 0) / Math.min(100, history.length) : 0.5;
            fitnessScores.set(name, fitness);
        }
        // 2. SÉLECTION
        const sortedAgents = Array.from(fitnessScores.entries()).sort((a, b) => b[1] - a[1]);
        const survivors = sortedAgents.slice(0, Math.ceil(this.agents.size * 0.7)).map(a => a[0]);
        const extinct = sortedAgents.slice(Math.ceil(this.agents.size * 0.7)).map(a => a[0]);
        // 3. EXTINCTION
        for (const name of extinct) {
            logger.info(`   ☠️ ${name} éteint → conservation gènes dans l'arche`);
            // this.arche.store(this.agents.get(name)!.genome);
            this.extinctionEvents++;
        }
        // 4. REPRODUCTION (Crossover)
        let newBorns = 0;
        for (let i = 0; i < extinct.length; i++) {
            const p1 = survivors[Math.floor(Math.random() * survivors.length)];
            const p2 = survivors[Math.floor(Math.random() * survivors.length)];
            const childName = `${p1}_${p2}_gen${this.generation}_${i}`;
            const child = this.crossover(this.agents.get(p1), this.agents.get(p2), childName);
            this.agents.set(childName, child);
            this.agents.delete(extinct[i]); // Replace extinct with newborn
            logger.info(`   🌱 ${childName} né de ${p1} × ${p2}`);
            newBorns++;
        }
        // 5. MUTATION GLOBALE
        for (const name of survivors) {
            if (Math.random() < 0.3) {
                const agent = this.agents.get(name);
                await agent.crispr.edit(agent.genome, Math.floor(Math.random() * 100), ChromosomeType.BEHAVIOR, 'gaussian');
            }
        }
        // 6. SYMBIOSE
        if (Math.random() < 0.1 && survivors.length >= 2) {
            const a1 = survivors[Math.floor(Math.random() * survivors.length)];
            let a2 = survivors[Math.floor(Math.random() * survivors.length)];
            while (a2 === a1)
                a2 = survivors[Math.floor(Math.random() * survivors.length)];
            this.symbiosis(this.agents.get(a1), this.agents.get(a2));
        }
        this.generation++;
        logger.info(`   📊 Stats: ${survivors.length} survivants, ${newBorns} nouveau-nés, ${this.extinctionEvents} extinctions, ${this.symbiosisCount} symbioses`);
    }
    crossover(p1, p2, childName) {
        const child = new EvolutionaryAgent(childName, this.arche, this.crispr);
        child.genome = p1.genome.clone();
        child.genome.agentName = childName;
        child.genome.generation = Math.max(p1.genome.generation, p2.genome.generation) + 1;
        // Crossover simple
        for (let i = 0; i < child.genome.g_struct.length; i++) {
            if (Math.random() > 0.5)
                child.genome.g_struct[i] = p2.genome.g_struct[i].clone();
        }
        child.genome.updateHash();
        return child;
    }
    symbiosis(a1, a2) {
        logger.info(`   🔗 SYMBIOSE DÉTECTÉE: ${a1.name} + ${a2.name}`);
        this.symbiosisCount++;
        // Fusion temporaire des fitness
        const w1 = a1.currentFitness;
        const w2 = a2.currentFitness;
        const total = w1 + w2 || 1;
        for (let i = 0; i < a1.genome.g_behavior.length; i++) {
            const val = (w1 * a1.genome.g_behavior[i].value + w2 * a2.genome.g_behavior[i].value) / total;
            a1.genome.g_behavior[i].value = val;
            a2.genome.g_behavior[i].value = val;
        }
    }
}
