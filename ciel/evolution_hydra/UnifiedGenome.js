/**
 * ═══════════════════════════════════════════════════════════════
 * UNIFIED GENOME — Source unique de vérité pour tous les génomes HYDRA
 * ═══════════════════════════════════════════════════════════════
 *
 * Cette classe unifie :
 * - V1 (Genome.ts)         : 4 chromosomes × 100 gènes, params simples
 * - V2 (GenomeV2.ts)       : épigénome, karma, ombre, résonance, méta-instructions
 * - V3 (TitanGenome.ts)    : 4 chromosomes × 18 432 gènes (mode titan)
 *
 * Mode par défaut : V1 (400 gènes au total, mémoire légère)
 * Mode titan      : 18 432 gènes au total (penser à l'empreinte RAM)
 *
 * Les anciens fichiers (Genome.ts, GenomeV2.ts, TitanGenome.ts) sont
 * des shims de compatibilité qui pointent vers cette classe.
 *
 * Pattern d'utilisation :
 * ```typescript
 * import { UnifiedGenome } from './UnifiedGenome.js';
 *
 * // Mode V1 (par défaut)
 * const g1 = new UnifiedGenome({ agentName: 'agent_1' });
 *
 * // Mode Titan (gros génome)
 * const g2 = new UnifiedGenome({ agentName: 'titan', titanSize: true });
 *
 * // Mode sans initialisation aléatoire (reprise depuis serialize)
 * const g3 = UnifiedGenome.deserialize(json);
 * ```
 */
import crypto from 'crypto';
import { HardwareMetrics } from '../utils/HardwareMetrics.js';
// ════════════════════════════════════════════════════════════
// TYPES & INTERFACES
// ════════════════════════════════════════════════════════════
export var ChromosomeType;
(function (ChromosomeType) {
    ChromosomeType["STRUCT"] = "STRUCT";
    ChromosomeType["BEHAVIOR"] = "BEHAVIOR";
    ChromosomeType["EPI"] = "EPI";
    ChromosomeType["META"] = "META";
})(ChromosomeType || (ChromosomeType = {}));
export class Gene {
    id;
    value;
    chromosome;
    mutable;
    // Marqueurs épigénétiques (hérités de V1 + V3)
    h3k4me3; // Activation (0-1)
    h3k27me3; // Répression (0-1)
    dna_methylation; // Méthylation (0-1)
    constructor(id, value, chromosome, mutable = true, h3k4me3 = 0.0, h3k27me3 = 0.0, dna_methylation = 0.0) {
        this.id = id;
        this.value = value;
        this.chromosome = chromosome;
        this.mutable = mutable;
        this.h3k4me3 = h3k4me3;
        this.h3k27me3 = h3k27me3;
        this.dna_methylation = dna_methylation;
    }
    /**
     * Expression génique avec modulation épigénétique.
     * - h3k27me3 > 0.7 → gène réprimé (valeur × 0.1)
     * - h3k4me3 > 0.7 → gène suractivé (valeur × 1.5)
     * - sinon       → valeur × (1 - dna_methylation)
     */
    express() {
        if (this.h3k27me3 > 0.7)
            return this.value * 0.1;
        if (this.h3k4me3 > 0.7)
            return this.value * 1.5;
        return this.value * (1.0 - this.dna_methylation);
    }
    clone() {
        return new Gene(this.id, this.value, this.chromosome, this.mutable, this.h3k4me3, this.h3k27me3, this.dna_methylation);
    }
}
// ════════════════════════════════════════════════════════════
// UNIFIED GENOME — LA CLASSE
// ════════════════════════════════════════════════════════════
export class UnifiedGenome {
    // Identité
    id = '';
    agentName;
    generation;
    dnaHash = '';
    // Fitness
    fitness = 0;
    fitnessHistory = [];
    mutationCount = 0;
    // Appartenance
    factionId;
    specialties = [];
    // Paramètres phénotypiques (unifiés V1 + V2)
    params;
    // 4 Chromosomes (toujours présents, taille variable)
    g_struct = [];
    g_behavior = [];
    g_epi = [];
    g_meta = [];
    // V2 : épigénétique
    epigenome = [];
    // V2 : karma
    karmicLedger = [];
    // V2 : ombre (jungienne)
    shadow;
    // V2 : résonance
    resonance;
    // V2 : méta-instructions
    metaInstructions = [];
    ancestorIds = [];
    isIndividuated = false;
    // Configuration interne
    _titanSize;
    _legacyV1;
    // ──────────────────────────────────────────────────────────
    // CONSTRUCTEUR
    // ──────────────────────────────────────────────────────────
    constructor(options = {}) {
        this.agentName = options.agentName ?? 'genome';
        this.generation = options.generation ?? 0;
        this.fitness = options.initialFitness ?? 0;
        this.ancestorIds = options.ancestorIds ?? [];
        this._titanSize = options.titanSize ?? false;
        this._legacyV1 = options.legacyV1 ?? false;
        this.params = this.makeDefaultParams(options.params);
        // Initialiser les chromosomes (sauf si on les charge depuis serialize)
        if (!options.noGenesis) {
            this.initGenesis();
        }
        // Initialiser les V2 features (sauf si legacyV1)
        if (!this._legacyV1) {
            this.epigenome = this.initializeEpigenome();
            this.karmicLedger = [];
            this.resonance = {
                frequency: this.params.resonanceFrequency,
                amplitude: 0.5,
                phase: Math.random() * Math.PI * 2,
                harmonics: [1, 1.618, 2.0],
            };
            this.shadow = {
                repressedTemperature: 2.0 - this.params.temperature,
                repressedTools: [],
                integrationLevel: 0,
                valence: 0,
            };
            this.checkSpecialties();
            this.updateShadowProfile();
        }
        else {
            // V1 legacy : on initialise quand même les V2 champs à des valeurs par défaut
            // pour que les méthodes ne crashent pas
            this.epigenome = [];
            this.karmicLedger = [];
            this.shadow = {
                repressedTemperature: 0,
                repressedTools: [],
                integrationLevel: 0,
                valence: 0,
            };
            this.resonance = {
                frequency: 1,
                amplitude: 0,
                phase: 0,
                harmonics: [1],
            };
        }
        this.updateHash();
        if (!this._legacyV1) {
            this.updatePhenotype();
        }
    }
    // ──────────────────────────────────────────────────────────
    // INITIALISATION
    // ──────────────────────────────────────────────────────────
    makeDefaultParams(overrides) {
        const defaults = {
            // V1
            temperature: 0.7,
            topP: 0.9,
            promptMutation: '',
            toolWeights: {
                'read_file': 1.0,
                'write_to_file': 1.0,
                'edit_file': 1.0,
                'list_dir_glob': 1.0,
                'web_search': 1.2,
                'web_fetch': 1.0,
                'run_command': 1.0,
                'universal_lab': 1.5,
            },
            episodicRetention: 0.5,
            environmentalSensitivity: 0.5,
            dockerAffinity: 0.4,
            polyglotDepth: 0.3,
            // V2
            resonanceFrequency: 1 + Math.random() * 9,
            shadowTolerance: 0.3 + Math.random() * 0.4,
            karmicWeight: 0.2 + Math.random() * 0.3,
            epigeneticSensitivity: 0.3 + Math.random() * 0.4,
            metamorphicPotential: 0.1 + Math.random() * 0.3,
            voidAttraction: 0.2 + Math.random() * 0.3,
        };
        return { ...defaults, ...overrides };
    }
    initGenesis() {
        const sizes = this._titanSize
            ? { struct: 4096, behavior: 8192, epi: 2048, meta: 4096 }
            : { struct: 100, behavior: 100, epi: 100, meta: 100 };
        // G-STRUCT
        for (let i = 0; i < sizes.struct; i++) {
            this.g_struct.push(new Gene(i, this.gaussianRandom(0.5, 0.1), ChromosomeType.STRUCT));
        }
        // G-BEHAVIOR
        for (let i = 0; i < sizes.behavior; i++) {
            this.g_behavior.push(new Gene(i, this.gaussianRandom(0.5, 0.15), ChromosomeType.BEHAVIOR));
        }
        // G-EPI (marqueurs initiaux 0.3/0.3 comme V1)
        for (let i = 0; i < sizes.epi; i++) {
            const g = new Gene(i, 0.5, ChromosomeType.EPI);
            g.h3k4me3 = 0.3;
            g.h3k27me3 = 0.3;
            this.g_epi.push(g);
        }
        // G-META
        for (let i = 0; i < sizes.meta; i++) {
            this.g_meta.push(new Gene(i, this.gaussianRandom(0.5, 0.05), ChromosomeType.META));
        }
    }
    initializeEpigenome() {
        return [
            { gene: 'temperature', active: true, methylation: 0.1, environmentalTrigger: 'HIGH_CPU', stability: 0.8 },
            { gene: 'polyglotDepth', active: true, methylation: 0.2, environmentalTrigger: 'NEW_LANGUAGE', stability: 0.7 },
            { gene: 'dockerAffinity', active: true, methylation: 0.15, environmentalTrigger: 'SECURITY_THREAT', stability: 0.9 },
            { gene: 'voidAttraction', active: true, methylation: 0.3, environmentalTrigger: 'STAGNATION', stability: 0.5 },
            { gene: 'metamorphicPotential', active: true, methylation: 0.25, environmentalTrigger: 'ARCHITECTURAL_CRISIS', stability: 0.6 },
        ];
    }
    // ──────────────────────────────────────────────────────────
    // HASH & PHÉNOTYPE
    // ──────────────────────────────────────────────────────────
    updateHash() {
        const data = `${this.agentName}:${this.generation}`;
        const sampleSize = Math.min(10, this.g_struct.length);
        let payload = data;
        for (let i = 0; i < sampleSize; i++) {
            payload += this.g_struct[i]?.value.toFixed(6) ?? '0.000000';
        }
        this.id = crypto.createHash('sha256').update(payload).digest('hex').substring(0, 16);
        this.dnaHash = this.id;
    }
    updatePhenotype() {
        if (this._legacyV1)
            return;
        const creativity = this.g_behavior[0]?.express() ?? 0.5;
        const prudence = this.g_behavior[1]?.express() ?? 0.5;
        this.params.temperature = 0.1 + (creativity * 0.8);
        this.params.dockerAffinity = this.g_meta[2]?.express() ?? 0.5;
        this.params.polyglotDepth = this.g_meta[3]?.express() ?? 0.5;
        this.params.toolWeights = {
            read_file: this.g_behavior[2]?.express() ?? 1.0,
            edit_file: this.g_behavior[3]?.express() ?? 1.0,
            run_command: this.g_behavior[4]?.express() ?? 1.0,
        };
        this.specialties = [];
        if (creativity > 0.6)
            this.specialties.push('Creative Thinking');
        if (prudence > 0.6)
            this.specialties.push('Rigorous Verification');
        if ((this.g_struct[0]?.express() ?? 0) > 0.5)
            this.specialties.push('Deep Architecture');
        this.params.promptMutation = `You naturally exhibit a ${creativity > prudence ? 'highly creative and divergent' : 'highly structured and cautious'} mindset.`;
    }
    /**
     * Phénotype observable — interface attendue par CRISPR_Titan, CloneCoordinator.
     */
    getPhenotype() {
        const sampleSize = Math.min(50, this.g_struct.length);
        let epiSum = 0;
        for (let i = 0; i < sampleSize; i++)
            epiSum += this.g_struct[i].express();
        const epiExpr = epiSum / sampleSize;
        return {
            num_layers: this.g_struct.length,
            exploration_rate: this.g_behavior[0]?.express() ?? 0.5,
            creativity_index: this.g_behavior[1]?.express() ?? 0.5,
            risk_tolerance: this.g_behavior[2]?.express() ?? 0.5,
            collaboration_drive: this.g_behavior[3]?.express() ?? 0.5,
            learning_rate: 1e-3,
            epi_expr: epiExpr,
            temperature: this.params.temperature,
            docker_affinity: this.params.dockerAffinity,
            void_attraction: this.params.voidAttraction,
            metamorphic_potential: this.params.metamorphicPotential,
        };
    }
    // ──────────────────────────────────────────────────────────
    // EXPRESSION (par chromosome/gène, pour outils externes)
    // ──────────────────────────────────────────────────────────
    express(chromosome, geneId) {
        const gene = this.getGene(chromosome, geneId);
        return gene ? gene.express() : 0;
    }
    getGene(chromosome, geneId) {
        const arr = this.getChromosome(chromosome);
        return arr[geneId] ?? null;
    }
    getChromosome(chromosome) {
        switch (chromosome) {
            case ChromosomeType.STRUCT: return this.g_struct;
            case ChromosomeType.BEHAVIOR: return this.g_behavior;
            case ChromosomeType.EPI: return this.g_epi;
            case ChromosomeType.META: return this.g_meta;
        }
    }
    // ──────────────────────────────────────────────────────────
    // MUTATIONS
    // ──────────────────────────────────────────────────────────
    /**
     * Mutation gaussienne simple (V1-style).
     * Affecte tous les chromosomes, intensity = écart-type du bruit.
     */
    mutate(intensity = 0.1) {
        const mutateGene = (gene) => {
            if (!gene.mutable)
                return;
            const delta = (Math.random() - 0.5) * intensity;
            gene.value = Math.max(0, Math.min(1, gene.value + delta));
        };
        [...this.g_struct, ...this.g_behavior, ...this.g_epi, ...this.g_meta].forEach(mutateGene);
        this.generation++;
        this.mutationCount++;
        this.updateHash();
        this.updatePhenotype();
    }
    /**
     * Mutation V2 (multi-dimensionnelle, hardware-driven).
     * Affecte params + épigénome + résonance.
     */
    mutateV2(rate = 0.1) {
        if (this._legacyV1) {
            this.mutate(rate);
            return;
        }
        let mutated = false;
        const entropy = () => HardwareMetrics.getPhysicalEntropyFloat();
        if (entropy() < rate) {
            this.params.temperature = Math.max(0, Math.min(2.0, this.params.temperature + (entropy() * 0.3 - 0.15)));
            mutated = true;
        }
        if (entropy() < rate) {
            this.params.resonanceFrequency = Math.max(0.1, Math.min(10, this.params.resonanceFrequency + (entropy() * 2 - 1)));
            mutated = true;
        }
        if (entropy() < rate) {
            this.params.shadowTolerance = Math.max(0, Math.min(1, this.params.shadowTolerance + (entropy() * 0.2 - 0.1)));
            mutated = true;
        }
        if (entropy() < rate) {
            this.params.voidAttraction = Math.max(0, Math.min(1, this.params.voidAttraction + (entropy() * 0.2 - 0.1)));
            mutated = true;
        }
        if (entropy() < rate) {
            this.params.metamorphicPotential = Math.max(0, Math.min(1, this.params.metamorphicPotential + (entropy() * 0.2 - 0.1)));
            mutated = true;
        }
        // Mutation épigénétique spontanée
        if (entropy() < rate * 0.5) {
            const marker = this.epigenome[Math.floor(Math.random() * this.epigenome.length)];
            if (marker) {
                marker.methylation = Math.max(0, Math.min(1, marker.methylation + (Math.random() * 0.3 - 0.15)));
                marker.active = marker.methylation < 0.5;
                mutated = true;
            }
        }
        // Mutation de résonance
        if (entropy() < rate * 0.3) {
            this.resonance.phase += (Math.random() * 0.5 - 0.25);
            this.resonance.amplitude = Math.max(0.1, Math.min(1.0, this.resonance.amplitude + (Math.random() * 0.2 - 0.1)));
            mutated = true;
        }
        if (mutated) {
            this.mutationCount++;
            this.checkSpecialties();
            this.updateShadowProfile();
        }
    }
    /**
     * Mutation selon une stratégie CRISPR (5 stratégies valides).
     */
    async mutateByStrategy(targetGeneId, chrom, strategy, geneBank) {
        const genes = this.getChromosome(chrom);
        const targetGene = genes[targetGeneId];
        if (!targetGene)
            return this;
        let newValue = targetGene.value;
        switch (strategy) {
            case 'gaussian':
                newValue = Math.max(0, Math.min(1, targetGene.value + (Math.random() - 0.5) * 0.1));
                break;
            case 'epigenetic':
                // Marquage sans changement de valeur
                targetGene.h3k4me3 = 0.9;
                targetGene.h3k27me3 = 0.1;
                return this;
            case 'sacrifice':
                newValue = 0.0;
                break;
            case 'transposon': {
                const sourceChroms = [ChromosomeType.STRUCT, ChromosomeType.BEHAVIOR, ChromosomeType.EPI, ChromosomeType.META];
                const sourceChrom = sourceChroms[Math.floor(Math.random() * sourceChroms.length)];
                const sourceGenes = this.getChromosome(sourceChrom);
                const sourceGene = sourceGenes[Math.floor(Math.random() * sourceGenes.length)];
                newValue = sourceGene?.value ?? newValue;
                break;
            }
            case 'bricolage':
                if (geneBank) {
                    const extinct = geneBank.resurrectGene(chrom, targetGeneId);
                    if (extinct)
                        newValue = extinct.value;
                }
                break;
        }
        targetGene.value = newValue;
        this.updateHash();
        this.updatePhenotype();
        return this;
    }
    // ──────────────────────────────────────────────────────────
    // CROSSOVER & FUSION
    // ──────────────────────────────────────────────────────────
    /**
     * Crossover V1-style : mixe 1 gène sur 2 entre parents.
     */
    crossover(other) {
        const child = this.clone();
        child.agentName = `${this.agentName}_${other.agentName}`;
        child.generation = Math.max(this.generation, other.generation) + 1;
        const mix = (target, source) => {
            const len = Math.min(target.length, source.length);
            for (let i = 0; i < len; i += 2) {
                target[i].value = source[i].value;
            }
        };
        mix(child.g_struct, other.g_struct);
        mix(child.g_behavior, other.g_behavior);
        mix(child.g_epi, other.g_epi);
        mix(child.g_meta, other.g_meta);
        child.fitness = (this.fitness + other.fitness) / 2;
        child.updateHash();
        child.updatePhenotype();
        return child;
    }
    /**
     * Fusion : combine les spécialités et les toolWeights.
     */
    fuseWith(other) {
        const fused = this.crossover(other);
        fused.specialties = [...new Set([...this.specialties, ...other.specialties])];
        fused.params.temperature = (this.params.temperature + other.params.temperature) / 2;
        fused.params.dockerAffinity = (this.params.dockerAffinity + other.params.dockerAffinity) / 2;
        fused.params.polyglotDepth = (this.params.polyglotDepth + other.params.polyglotDepth) / 2;
        fused.params.toolWeights = { ...this.params.toolWeights, ...other.params.toolWeights };
        return fused;
    }
    // ──────────────────────────────────────────────────────────
    // V2 : KARMA
    // ──────────────────────────────────────────────────────────
    recordKarma(action, outcome, impact, lesson) {
        this.karmicLedger.push({
            id: `karma_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`,
            action,
            outcome,
            impact,
            generation: this.generation,
            lesson,
            timestamp: Date.now(),
        });
        if (this.karmicLedger.length > 100) {
            this.karmicLedger = this.karmicLedger.slice(-50);
        }
    }
    consultKarma(proposedAction) {
        const relevant = this.karmicLedger.filter(k => k.action.toLowerCase().includes(proposedAction.toLowerCase().split(' ')[0] ?? ''));
        if (relevant.length === 0) {
            return { bias: 0, wisdom: 'No karmic precedent for this action.' };
        }
        const success = relevant.filter(k => k.outcome === 'SUCCESS').length;
        const failure = relevant.filter(k => k.outcome === 'FAILURE').length;
        const bias = (success - failure) / relevant.length * this.params.karmicWeight;
        const bestLesson = [...relevant].sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))[0];
        return {
            bias,
            wisdom: bestLesson?.lesson || 'Karmic records are ambiguous.',
        };
    }
    // ──────────────────────────────────────────────────────────
    // V2 : ÉPIGÉNÉTIQUE
    // ──────────────────────────────────────────────────────────
    applyEpigeneticTrigger(trigger) {
        for (const marker of this.epigenome) {
            if (marker.environmentalTrigger === trigger) {
                const entropy = HardwareMetrics.getPhysicalEntropyFloat();
                if (entropy < 0.3) {
                    marker.active = !marker.active;
                    marker.methylation = marker.active ? 0.1 : 0.9;
                    if (marker.gene === 'temperature' && !marker.active) {
                        this.params.temperature *= 0.8;
                    }
                    if (marker.gene === 'voidAttraction' && marker.active) {
                        this.params.voidAttraction = Math.min(1.0, this.params.voidAttraction + 0.1);
                    }
                }
            }
        }
    }
    // ──────────────────────────────────────────────────────────
    // V2 : RÉSONANCE
    // ──────────────────────────────────────────────────────────
    computeResonanceWith(other) {
        const freqRatio = this.resonance.frequency / (other.resonance.frequency + 0.01);
        const harmonicRatios = [1.0, 1.5, 1.618, 2.0, 3.0];
        let maxResonance = 0;
        for (const hr of harmonicRatios) {
            const deviation = Math.abs(freqRatio - hr) / hr;
            if (deviation < 0.15) {
                maxResonance = Math.max(maxResonance, 1 - deviation * 5);
            }
        }
        const phaseAlignment = Math.cos(this.resonance.phase - other.resonance.phase);
        return maxResonance * 0.7 + (phaseAlignment * 0.5 + 0.5) * 0.3;
    }
    // ──────────────────────────────────────────────────────────
    // V2 : OMBRE
    // ──────────────────────────────────────────────────────────
    updateShadowProfile() {
        if (this._legacyV1)
            return;
        this.shadow.repressedTemperature = 2.0 - this.params.temperature;
        const toolEntries = Object.entries(this.params.toolWeights);
        const avgWeight = toolEntries.reduce((a, [, w]) => a + w, 0) / Math.max(toolEntries.length, 1);
        this.shadow.repressedTools = toolEntries.filter(([, w]) => w < avgWeight).map(([t]) => t);
        const tempDelta = Math.abs(this.shadow.repressedTemperature - this.params.temperature);
        this.shadow.valence = tempDelta > 1.0 ? -0.5 : 0.5;
        this.shadow.integrationLevel = this.params.shadowTolerance;
    }
    // ──────────────────────────────────────────────────────────
    // V2 : SPÉCIALITÉS
    // ──────────────────────────────────────────────────────────
    checkSpecialties() {
        if (this._legacyV1)
            return;
        for (const [tool, weight] of Object.entries(this.params.toolWeights)) {
            if (weight > 1.8 && !this.specialties.includes(`Master of ${tool}`)) {
                this.specialties.push(`Master of ${tool}`);
            }
        }
        if (this.params.temperature > 1.5 && !this.specialties.includes('Creative Chaos')) {
            this.specialties.push('Creative Chaos');
        }
        if (this.params.temperature < 0.2 && !this.specialties.includes('Absolute Logic')) {
            this.specialties.push('Absolute Logic');
        }
        if (this.params.voidAttraction > 0.7 && !this.specialties.includes('Void Walker')) {
            this.specialties.push('Void Walker');
        }
        if (this.params.metamorphicPotential > 0.7 && !this.specialties.includes('Meta-Architect')) {
            this.specialties.push('Meta-Architect');
        }
        if (this.params.shadowTolerance > 0.8 && !this.specialties.includes('Shadow Integrated')) {
            this.specialties.push('Shadow Integrated');
        }
        if (this.params.resonanceFrequency > 8.0 && !this.specialties.includes('High Frequency Resonator')) {
            this.specialties.push('High Frequency Resonator');
        }
        if (this.karmicLedger.length > 20 && !this.specialties.includes('Karmic Sage')) {
            this.specialties.push('Karmic Sage');
        }
    }
    // ──────────────────────────────────────────────────────────
    // CLONE & SERIALIZATION
    // ──────────────────────────────────────────────────────────
    clone() {
        const copy = new UnifiedGenome({
            agentName: this.agentName,
            generation: this.generation,
            params: { ...this.params, toolWeights: { ...this.params.toolWeights } },
            titanSize: this._titanSize,
            legacyV1: this._legacyV1,
            ancestorIds: [...this.ancestorIds],
            noGenesis: true,
        });
        copy.id = this.id;
        copy.dnaHash = this.dnaHash;
        copy.fitness = this.fitness;
        copy.fitnessHistory = [...this.fitnessHistory];
        copy.mutationCount = this.mutationCount;
        copy.factionId = this.factionId;
        copy.specialties = [...this.specialties];
        copy.g_struct = this.g_struct.map(g => g.clone());
        copy.g_behavior = this.g_behavior.map(g => g.clone());
        copy.g_epi = this.g_epi.map(g => g.clone());
        copy.g_meta = this.g_meta.map(g => g.clone());
        copy.epigenome = this.epigenome.map(m => ({ ...m }));
        copy.karmicLedger = this.karmicLedger.map(k => ({ ...k }));
        copy.shadow = { ...this.shadow, repressedTools: [...this.shadow.repressedTools] };
        copy.resonance = { ...this.resonance, harmonics: [...this.resonance.harmonics] };
        copy.metaInstructions = [...this.metaInstructions];
        copy.isIndividuated = this.isIndividuated;
        return copy;
    }
    serialize() {
        return JSON.stringify({
            id: this.id,
            name: this.agentName,
            generation: this.generation,
            fitness: this.fitness,
            fitnessHistory: this.fitnessHistory,
            traits: this.specialties,
            params: this.params,
            chromosomes: {
                struct: this.g_struct.length,
                behavior: this.g_behavior.length,
                epi: this.g_epi.length,
                meta: this.g_meta.length,
            },
            karmicLedgerSize: this.karmicLedger.length,
        });
    }
    static deserialize(json) {
        const data = JSON.parse(json);
        return new UnifiedGenome({
            agentName: data.name,
            generation: data.gen,
            initialFitness: data.fitness ?? 0,
            params: data.params,
            noGenesis: false,
        });
    }
    // ──────────────────────────────────────────────────────────
    // FITNESS
    // ──────────────────────────────────────────────────────────
    /**
     * Fitness composite : combine historique + cohérence.
     * Sera remplacé par FitnessEvaluator en Phase 1.3.
     */
    fitnessScore() {
        if (this.fitnessHistory.length === 0)
            return this.fitness || 0.5;
        const recent = this.fitnessHistory.slice(-10);
        return recent.reduce((a, b) => a + b, 0) / recent.length;
    }
    // ──────────────────────────────────────────────────────────
    // UTILITAIRES
    // ──────────────────────────────────────────────────────────
    /**
     * Box-Muller transform — distribution gaussienne clampée [0, 1].
     */
    gaussianRandom(mean, stdev) {
        const u = 1 - Math.random();
        const v = Math.random();
        const z = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
        return Math.max(0, Math.min(1, z * stdev + mean));
    }
    /** Indique si ce génome est en mode Titan (gros chromosomes). */
    isTitanSize() {
        return this._titanSize;
    }
    /** Indique si ce génome est en mode legacy V1 (sans V2 features actives). */
    isLegacyV1() {
        return this._legacyV1;
    }
}
