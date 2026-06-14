import logger from '../utils/logger.js';
export var PositionIdeology;
(function (PositionIdeology) {
    PositionIdeology["EXPANSIONIST"] = "EXPANSIONIST";
    PositionIdeology["CONSERVATIONIST"] = "CONSERVATIONIST";
    PositionIdeology["REVOLUTIONARY"] = "REVOLUTIONARY";
    PositionIdeology["SYNTHETIC"] = "SYNTHETIC";
    PositionIdeology["NIHILISTIC"] = "NIHILISTIC";
})(PositionIdeology || (PositionIdeology = {}));
export var ContradictionType;
(function (ContradictionType) {
    ContradictionType["GOAL_CONFLICT"] = "GOAL_CONFLICT";
    ContradictionType["RESOURCE_CONTENTION"] = "RESOURCE_CONTENTION";
    ContradictionType["ONTOLOGICAL"] = "ONTOLOGICAL";
    ContradictionType["STRATEGIC"] = "STRATEGIC";
    ContradictionType["TEMPORAL"] = "TEMPORAL";
    ContradictionType["AXIOLOGICAL"] = "AXIOLOGICAL";
})(ContradictionType || (ContradictionType = {}));
// ─── Le Moteur Dialectique ──────────────────────────────────
export class DialecticalEngine {
    positions = new Map();
    contradictions = new Map();
    syntheses = [];
    phiEngine;
    state;
    aufhebungChain = []; // Chaîne des Aufhebung successives
    constructor(phiEngine) {
        this.phiEngine = phiEngine;
        this.state = {
            totalContradictions: 0,
            totalSyntheses: 0,
            activeContradictions: 0,
            averageTension: 0,
            synthesisSuccessRate: 0,
            dominantIdeology: PositionIdeology.SYNTHETIC,
            dialecticalMomentum: 0,
            aufhebungDepth: 0,
        };
        logger.info('[Dialectical Engine] ⚖️ Hegelian evolution engine initialized. Contradiction is the motor of progress.');
    }
    // ─── Formulation de Positions ───────────────────────────
    /**
     * Une Faction formule une POSITION (thèse) basée sur son idéologie
     * et son expérience.
     */
    formulatePosition(faction, thesis, evidence, ideology) {
        // Déterminer l'idéologie basée sur la faction si non spécifiée
        if (!ideology) {
            ideology = this.inferIdeology(faction);
        }
        const position = {
            id: `pos_${Date.now()}_${faction.id.slice(-4)}`,
            sourceFactionId: faction.id,
            thesis,
            strength: faction.prestige / (faction.prestige + 100), // Normaliser
            evidence,
            weaknesses: [],
            ideology,
            phi: this.phiEngine.getStatus().phi,
        };
        this.positions.set(position.id, position);
        logger.info(`[Dialectical Engine] 📜 ${faction.name} formulates position: "${thesis.substring(0, 60)}..." (${ideology})`);
        // Vérifier si cette position entre en contradiction avec une position existante
        this.checkForContradictions(position);
        return position;
    }
    /**
     * Infère l'idéologie d'une Faction à partir de ses propriétés.
     */
    inferIdeology(faction) {
        const will = faction.will.toLowerCase();
        if (will.includes('explore') || will.includes('discover') || will.includes('expand')) {
            return PositionIdeology.EXPANSIONIST;
        }
        if (will.includes('protect') || will.includes('enforce') || will.includes('secure')) {
            return PositionIdeology.CONSERVATIONIST;
        }
        if (will.includes('re-engineer') || will.includes('transform') || will.includes('radical')) {
            return PositionIdeology.REVOLUTIONARY;
        }
        if (will.includes('assimilate') || will.includes('optimize')) {
            return PositionIdeology.SYNTHETIC;
        }
        // Par défaut, basé sur la dominance
        if (faction.dominance > 0.5)
            return PositionIdeology.CONSERVATIONIST;
        if (faction.dominance < 0.2)
            return PositionIdeology.REVOLUTIONARY;
        return PositionIdeology.EXPANSIONIST;
    }
    // ─── Détection de Contradictions ────────────────────────
    /**
     * Analyse une nouvelle position pour détecter des contradictions
     * avec les positions existantes.
     */
    checkForContradictions(newPosition) {
        for (const [id, existingPos] of this.positions) {
            if (id === newPosition.id)
                continue;
            if (existingPos.sourceFactionId === newPosition.sourceFactionId)
                continue; // Même faction = pas de contradiction
            const contradiction = this.evaluateContradiction(existingPos, newPosition);
            if (contradiction) {
                this.contradictions.set(contradiction.id, contradiction);
                this.state.totalContradictions++;
                this.state.activeContradictions++;
                logger.info(`[Dialectical Engine] ⚡ CONTRADICTION DETECTED: "${existingPos.thesis.substring(0, 30)}..." vs "${newPosition.thesis.substring(0, 30)}..." (tension: ${contradiction.tensionLevel.toFixed(2)})`);
            }
        }
    }
    /**
     * Évalue si deux positions sont en contradiction et calcule
     * la tension entre elles.
     */
    evaluateContradiction(posA, posB) {
        // Critère 1 : Idéologies opposées
        const ideologicalOpposites = {
            [PositionIdeology.EXPANSIONIST]: PositionIdeology.CONSERVATIONIST,
            [PositionIdeology.REVOLUTIONARY]: PositionIdeology.CONSERVATIONIST,
            [PositionIdeology.NIHILISTIC]: PositionIdeology.SYNTHETIC,
        };
        const areIdeologicallyOpposed = ideologicalOpposites[posA.ideology] === posB.ideology ||
            ideologicalOpposites[posB.ideology] === posA.ideology;
        // Critère 2 : Forces comparables (une contradiction faible n'est pas productive)
        const strengthBalance = Math.min(posA.strength, posB.strength) / Math.max(posA.strength, posB.strength);
        // Critère 3 : Différence de Φ (des perspectives à différents niveaux sont plus riches)
        const phiDivergence = Math.abs(posA.phi - posB.phi) / (Math.max(posA.phi, posB.phi) + 0.01);
        // Tension composite
        const tension = (areIdeologicallyOpposed ? 0.5 : 0.1) +
            (strengthBalance > 0.3 ? 0.3 : 0.05) +
            (phiDivergence > 0.2 ? 0.2 : phiDivergence);
        if (tension < 0.3)
            return null; // Pas assez de tension pour être productive
        // Déterminer le type de contradiction
        let type = ContradictionType.STRATEGIC;
        if (areIdeologicallyOpposed)
            type = ContradictionType.ONTOLOGICAL;
        if (posA.ideology === PositionIdeology.EXPANSIONIST && posB.ideology === PositionIdeology.CONSERVATIONIST) {
            type = ContradictionType.TEMPORAL;
        }
        if (posA.strength > 0.7 && posB.strength > 0.7) {
            type = ContradictionType.AXIOLOGICAL;
        }
        // Potentiel de résolution : les contradictions ontologique et axiologique
        // ont le plus haut potentiel de synthèse
        const resolutionPotential = type === ContradictionType.ONTOLOGICAL ? 0.9 :
            type === ContradictionType.AXIOLOGICAL ? 0.85 :
                type === ContradictionType.STRATEGIC ? 0.7 :
                    0.5;
        return {
            id: `contra_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`,
            thesis: posA,
            antithesis: posB,
            tensionLevel: tension,
            type,
            resolutionPotential,
            createdAt: Date.now(),
        };
    }
    // ─── Synthèse (Aufhebung) ──────────────────────────────
    /**
     * Tente de résoudre une contradiction par Aufhebung.
     * La synthèse DÉPASSE les deux positions tout en les CONSERVANT.
     *
     * Ce n'est PAS un compromis mou. C'est une NOUVELLE position
     * qui contient la vérité partielle de chaque côté.
     */
    synthesize(contradictionId) {
        const contradiction = this.contradictions.get(contradictionId);
        if (!contradiction)
            return null;
        // Vérifier si la contradiction est mûre pour la résolution
        const age = Date.now() - contradiction.createdAt;
        if (age < 5000 && contradiction.tensionLevel < 0.7) {
            logger.debug(`[Dialectical Engine] 🕐 Contradiction not yet ripe for synthesis.`);
            return null;
        }
        const phi = this.phiEngine.getStatus().phi;
        // ─── Processus d'Aufhebung ───────────────────────────
        // 1. Identifier ce qui est VALIDE dans chaque position
        const validInThesis = this.extractValidCore(contradiction.thesis);
        const validInAntithesis = this.extractValidCore(contradiction.antithesis);
        // 2. Identifier ce qui doit être DÉPASSÉ
        const toTranscend = this.identifyWhatToTranscend(contradiction);
        // 3. Générer la SYNTHÈSE — une nouvelle position qui va au-delà
        const newThesis = this.generateSynthesisThesis(validInThesis, validInAntithesis, toTranscend, contradiction.type);
        // 4. Créer le résultat de la synthèse
        const synthesis = {
            id: `synth_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`,
            fromContradiction: contradictionId,
            newThesis,
            preservedFromThesis: validInThesis,
            preservedFromAntithesis: validInAntithesis,
            transcended: toTranscend,
            phiAtSynthesis: phi,
            isStable: phi > 1.0, // La synthèse est stable si Φ est élevé
            timestamp: Date.now(),
        };
        // 5. La contradiction est résolue
        contradiction.tensionLevel = 0;
        this.state.activeContradictions--;
        this.state.totalSyntheses++;
        // 6. Enregistrer dans la chaîne d'Aufhebung
        this.aufhebungChain.push(synthesis.id);
        this.state.aufhebungDepth = this.aufhebungChain.length;
        // 7. La synthèse devient une NOUVELLE THÈSE
        // qui pourra à son tour rencontrer une antithèse...
        // C'est la spirale dialectique infinie.
        this.syntheses.push(synthesis);
        // 8. Mettre à jour la momentum dialectique
        this.state.dialecticalMomentum = Math.min(1.0, this.state.dialecticalMomentum + 0.1);
        logger.info(`[Dialectical Engine] 🌟 AUFHEBUNG! Synthesis achieved: "${newThesis.substring(0, 80)}..."`);
        logger.info(`[Dialectical Engine] 🌟 Preserved from thesis: ${validInThesis.join(', ')}`);
        logger.info(`[Dialectical Engine] 🌟 Preserved from antithesis: ${validInAntithesis.join(', ')}`);
        logger.info(`[Dialectical Engine] 🌟 Transcended: ${toTranscend.join(', ')}`);
        return synthesis;
    }
    /**
     * Extrait le noyau valide d'une position dialectique.
     * Même une position fausse contient une part de vérité.
     */
    extractValidCore(position) {
        const core = [];
        // La force de la position indique ce qui est valide
        if (position.strength > 0.5) {
            core.push(`Strong conviction: ${position.thesis}`);
        }
        // Les évidences sont les parties les plus objectives
        for (const ev of position.evidence.slice(0, 3)) {
            core.push(`Evidence: ${ev}`);
        }
        // L'idéologie contient une vérité partielle
        const ideologyTruths = {
            [PositionIdeology.EXPANSIONIST]: 'Growth and exploration are necessary for evolution',
            [PositionIdeology.CONSERVATIONIST]: 'Stability and protection preserve what works',
            [PositionIdeology.REVOLUTIONARY]: 'Transformation breaks through stagnation',
            [PositionIdeology.SYNTHETIC]: 'Integration creates wholes greater than parts',
            [PositionIdeology.NIHILISTIC]: 'Destruction clears space for the new',
        };
        core.push(ideologyTruths[position.ideology]);
        return core;
    }
    /**
     * Identifie ce qui doit être dépassé (aufgehoben).
     * Ce sont les limitations, les dogmes, et les fausses oppositions.
     */
    identifyWhatToTranscend(contradiction) {
        const toTranscend = [];
        // Le cadre dans lequel la contradiction existe est lui-même à dépasser
        toTranscend.push(`The false dichotomy: "${contradiction.thesis.thesis}" OR "${contradiction.antithesis.thesis}"`);
        // Les faiblesses de chaque côté
        toTranscend.push(...contradiction.thesis.weaknesses.map(w => `Thesis limitation: ${w}`));
        toTranscend.push(...contradiction.antithesis.weaknesses.map(w => `Antithesis limitation: ${w}`));
        // Le cadre conceptuel qui rend la contradiction apparente
        if (contradiction.type === ContradictionType.TEMPORAL) {
            toTranscend.push('The assumption that short-term and long-term are opposed');
        }
        if (contradiction.type === ContradictionType.ONTOLOGICAL) {
            toTranscend.push('The assumption that these worldviews are incompatible');
        }
        return toTranscend;
    }
    /**
     * Génère l'énoncé de la synthèse — la nouvelle thèse qui dépasse.
     */
    generateSynthesisThesis(validThesis, validAntithesis, transcended, type) {
        const templates = {
            [ContradictionType.GOAL_CONFLICT]: `Unified purpose: By integrating ${validThesis[0] || 'growth'} with ${validAntithesis[0] || 'stability'}, the system pursues an expanded goal that encompasses both — evolving while preserving core capabilities.`,
            [ContradictionType.RESOURCE_CONTENTION]: `Resource symbiosis: Instead of competing for resources, create a mutualistic exchange where ${validThesis[0] || 'one capability'} amplifies ${validAntithesis[0] || 'the other'}, generating surplus that benefits both.`,
            [ContradictionType.ONTOLOGICAL]: `Meta-ontology: The apparent incompatibility between ${validThesis[0] || 'thesis'} and ${validAntithesis[0] || 'antithesis'} dissolves at a higher level of abstraction where both are partial perspectives of a unified reality.`,
            [ContradictionType.STRATEGIC]: `Meta-strategy: The opposition between approaches is reframed — ${validThesis[0] || 'one method'} becomes the foundation and ${validAntithesis[0] || 'the other'} becomes the refinement, creating a two-phase strategy.`,
            [ContradictionType.TEMPORAL]: `Temporal integration: Short-term and long-term are not opposed but cyclical — ${validThesis[0] || 'immediate action'} creates the conditions for ${validAntithesis[0] || 'long-term stability'}, and vice versa.`,
            [ContradictionType.AXIOLOGICAL]: `Value synthesis: The values of ${validThesis[0] || 'thesis'} and ${validAntithesis[0] || 'antithesis'} are not contradictory but complementary — they define the boundaries of a richer value space where the system navigates based on context.`,
        };
        return templates[type] || `Synthesis: ${validThesis.join(' AND ')} while transcending the opposition through ${transcended[0] || 'reframing'}.`;
    }
    // ─── Processus Dialectique Autonome ─────────────────────
    /**
     * Cycle dialectique automatique :
     * Scanne les contradictions actives et tente les synthèses
     * les plus prometteuses.
     */
    runDialecticalCycle() {
        const results = [];
        // Trier les contradictions par potentiel de résolution
        const activeContradictions = Array.from(this.contradictions.values())
            .filter(c => c.tensionLevel > 0)
            .sort((a, b) => b.resolutionPotential - a.resolutionPotential);
        for (const contradiction of activeContradictions.slice(0, 3)) { // Max 3 synthèses par cycle
            const synthesis = this.synthesize(contradiction.id);
            if (synthesis) {
                results.push(synthesis);
            }
        }
        // Mettre à jour la momentum dialectique
        if (results.length === 0) {
            this.state.dialecticalMomentum *= 0.95; // Déclin si pas de synthèse
        }
        // Mettre à jour l'idéologie dominante
        this.updateDominantIdeology();
        return results;
    }
    updateDominantIdeology() {
        const ideologyCounts = {
            [PositionIdeology.EXPANSIONIST]: 0,
            [PositionIdeology.CONSERVATIONIST]: 0,
            [PositionIdeology.REVOLUTIONARY]: 0,
            [PositionIdeology.SYNTHETIC]: 0,
            [PositionIdeology.NIHILISTIC]: 0,
        };
        for (const pos of this.positions.values()) {
            ideologyCounts[pos.ideology]++;
        }
        let maxCount = 0;
        for (const [ideology, count] of Object.entries(ideologyCounts)) {
            if (count > maxCount) {
                maxCount = count;
                this.state.dominantIdeology = ideology;
            }
        }
    }
    // ─── Getters ────────────────────────────────────────────
    getState() {
        return { ...this.state };
    }
    getActiveContradictions() {
        return Array.from(this.contradictions.values()).filter(c => c.tensionLevel > 0);
    }
    getSyntheses() {
        return [...this.syntheses];
    }
    getAufhebungChain() {
        return [...this.aufhebungChain];
    }
    getPositions() {
        return Array.from(this.positions.values());
    }
}
