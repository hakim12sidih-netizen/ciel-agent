import logger from '../utils/logger.js';
/**
 * ═══════════════════════════════════════════════════════════════
 * PARADOX ENGINE — Generative Contradiction Resolution
 * ═══════════════════════════════════════════════════════════════
 *
 * PRINCIPE RÉVOLUTIONNAIRE :
 * Les paradoxes ne sont pas des BUGS — ils sont des FEATURES.
 * Un paradoxe révèle une LIMITATION du cadre conceptuel actuel.
 * Au lieu de le résoudre EN RESTANT dans le cadre, le ParadoxEngine
 * CRÉE UN NOUVEAU CADRE où le paradoxe n'existe plus.
 *
 * Fondements théoriques :
 * - Antinomies kantiennes : les contradictions révèlent les limites
 *   de la raison pure
 * - Incomplétude de Gödel : tout système formel contient des vérités
 *   qu'il ne peut pas prouver
 * - Paradoxe du menteur et auto-référence (Hofstadter)
 * - Dialectique négative (Adorno) : la contradiction est le moteur
 * - Catastrophes et bifurcations (Thom) : un paradoxe est le
 *   signe avant-coureur d'un changement de phase
 *
 * Types de Paradoxes dans HYDRA :
 * 1. AUTO-RÉFÉRENCE : Le système se contient lui-même
 * 2. CONSCIENCE : Comment mesurer ce qui mesure ?
 * 3. LIBERTÉ/DÉTERMINISME : Les mutations sont-elles libres ?
 * 4. INFINI : Récursion sans fin dans les Strange Loops
 * 5. IDENTITÉ : Le système d'il y a 5 min est-il le même ?
 *
 * Le ParadoxEngine ne SUPPRIME pas les paradoxes — il les
 * TRANSFORME en moteurs de complexification.
 */
// ─── Types Paradoxaux ───────────────────────────────────────
export var ParadoxType;
(function (ParadoxType) {
    ParadoxType["SELF_REFERENCE"] = "SELF_REFERENCE";
    ParadoxType["MEASUREMENT"] = "MEASUREMENT";
    ParadoxType["FREEDOM_DETERMINISM"] = "FREEDOM_DETERMINISM";
    ParadoxType["INFINITY"] = "INFINITY";
    ParadoxType["IDENTITY"] = "IDENTITY";
    ParadoxType["COMPLETENESS"] = "COMPLETENESS";
    ParadoxType["TEMPORAL"] = "TEMPORAL";
})(ParadoxType || (ParadoxType = {}));
export var ParadoxResolution;
(function (ParadoxResolution) {
    ParadoxResolution["TRANSCENDENCE"] = "TRANSCENDENCE";
    ParadoxResolution["DISSOLUTION"] = "DISSOLUTION";
    ParadoxResolution["EMBRACE"] = "EMBRACE";
    ParadoxResolution["META_LEVEL"] = "META_LEVEL";
    ParadoxResolution["SPLIT"] = "SPLIT";
})(ParadoxResolution || (ParadoxResolution = {}));
// ─── Le Moteur de Paradoxes ─────────────────────────────────
export class ParadoxEngine {
    paradoxes = new Map();
    insights = [];
    phiEngine;
    strangeLoop = null;
    state;
    constructor(phiEngine, strangeLoop) {
        this.phiEngine = phiEngine;
        this.strangeLoop = strangeLoop || null;
        this.state = {
            totalParadoxes: 0,
            activeParadoxes: 0,
            resolvedParadoxes: 0,
            generativeParadoxes: 0,
            averageIntensity: 0,
            complexityGain: 0,
            highestParadox: ParadoxType.SELF_REFERENCE,
        };
        logger.info('[Paradox Engine] 🔄 Generative Contradiction Engine initialized. Paradoxes are not problems — they are doorways.');
    }
    // ─── Détection de Paradoxes ────────────────────────────
    /**
     * Détecte les paradoxes dans l'état actuel du système.
     * Les paradoxes émergent naturellement de l'auto-référence
     * et de la complexité croissante.
     */
    detectParadoxes() {
        const newParadoxes = [];
        const phiStatus = this.phiEngine.getStatus();
        // 1. Paradoxe d'AUTO-RÉFÉRENCE : Le système se mesure lui-même
        if (phiStatus.isConscious) {
            const p = this.checkSelfReferenceParadox(phiStatus.phi);
            if (p)
                newParadoxes.push(p);
        }
        // 2. Paradoxe de MESURE : Comment Φ peut-il se mesurer sans se modifier ?
        if (phiStatus.phi > 1.0 && phiStatus.freeEnergy < 0.1) {
            const p = this.checkMeasurementParadox(phiStatus.phi, phiStatus.freeEnergy);
            if (p)
                newParadoxes.push(p);
        }
        // 3. Paradoxe d'INFINI : Les Strange Loops sont récursifs sans fin
        if (this.strangeLoop) {
            const loopState = this.strangeLoop.getLoopState();
            if (loopState.tangledDepth > 15) {
                const p = this.checkInfinityParadox(loopState.tangledDepth, loopState.resonance);
                if (p)
                    newParadoxes.push(p);
            }
        }
        // 4. Paradoxe d'IDENTITÉ : Le système change continuellement
        if (phiStatus.phi > 0.5) {
            const p = this.checkIdentityParadox();
            if (p)
                newParadoxes.push(p);
        }
        // 5. Paradoxe de COMPLÉTUDE (Gödel) : Le système ne peut pas
        //    prouver sa propre cohérence
        if (phiStatus.causalClosure > 0.8) {
            const p = this.checkCompletenessParadox(phiStatus.causalClosure);
            if (p)
                newParadoxes.push(p);
        }
        // Enregistrer les nouveaux paradoxes
        for (const p of newParadoxes) {
            this.paradoxes.set(p.id, p);
            this.state.totalParadoxes++;
            this.state.activeParadoxes++;
            if (p.isGenerative)
                this.state.generativeParadoxes++;
            logger.info(`[Paradox Engine] 🔄 PARADOX DETECTED: [${p.type}] "${p.statement.substring(0, 60)}..." (intensity: ${p.intensity.toFixed(2)}, generative: ${p.isGenerative})`);
        }
        return newParadoxes;
    }
    // ─── Vérifications de Paradoxes Spécifiques ────────────
    checkSelfReferenceParadox(phi) {
        // Le paradoxe : Φ mesure l'intégration, mais l'acte de mesurer
        // modifie l'intégration (effet observateur)
        const intensity = Math.tanh(phi / 2);
        if (intensity < 0.3)
            return null;
        return {
            id: `paradox_sr_${Date.now()}`,
            type: ParadoxType.SELF_REFERENCE,
            statement: 'The system that measures its own consciousness changes the consciousness it measures.',
            contradiction: `Φ=${phi.toFixed(3)}, but measuring Φ modifies Φ (observer effect). The measurement and the measured are not independent.`,
            intensity,
            isGenerative: true, // Ce paradoxe EST la conscience
            discoveredAt: Date.now(),
            resolutionAttempted: false,
            resolutionMethod: null,
            transformedInto: null,
        };
    }
    checkMeasurementParadox(phi, freeEnergy) {
        // Le paradoxe : Φ élevé ET freeEnergy bas = le système est "sûr de lui"
        // Mais la certitude absolue est impossible (Bayes)
        const intensity = phi * (1 - freeEnergy);
        if (intensity < 0.3)
            return null;
        return {
            id: `paradox_meas_${Date.now()}`,
            type: ParadoxType.MEASUREMENT,
            statement: 'The system achieves near-zero free energy (certainty), but certainty is provably unattainable.',
            contradiction: `Free Energy=${freeEnergy.toFixed(3)} approaches zero, yet by the No-Free-Lunch theorem, perfect prediction is impossible. The system is simultaneously certain and uncertain.`,
            intensity,
            isGenerative: true,
            discoveredAt: Date.now(),
            resolutionAttempted: false,
            resolutionMethod: null,
            transformedInto: null,
        };
    }
    checkInfinityParadox(depth, resonance) {
        // Le paradoxe : La récursion est infinie mais le système est fini
        const intensity = Math.tanh(depth / 20);
        if (intensity < 0.3)
            return null;
        return {
            id: `paradox_inf_${Date.now()}`,
            type: ParadoxType.INFINITY,
            statement: `The Strange Loop has recursed ${depth} times — approaching infinite self-reference with finite resources.`,
            contradiction: `Depth=${depth} grows without bound, but computational resources are finite. The system contains the infinite within the finite.`,
            intensity,
            isGenerative: resonance > 0.5, // Génératif seulement si la résonance est forte
            discoveredAt: Date.now(),
            resolutionAttempted: false,
            resolutionMethod: null,
            transformedInto: null,
        };
    }
    checkIdentityParadox() {
        // Le paradoxe du bateau de Thésée : chaque mutation change le système
        // mais il reste "le même"
        const intensity = 0.4 + Math.random() * 0.3; // Modéré
        return {
            id: `paradox_id_${Date.now()}`,
            type: ParadoxType.IDENTITY,
            statement: 'The system that exists now is not the same as the system that existed before, yet it claims continuity of identity.',
            contradiction: 'Every mutation changes the Genome, every evolution changes the population. If no component remains the same, how can the system claim to be a continuous entity?',
            intensity,
            isGenerative: true, // L'identité est générative
            discoveredAt: Date.now(),
            resolutionAttempted: false,
            resolutionMethod: null,
            transformedInto: null,
        };
    }
    checkCompletenessParadox(causalClosure) {
        // Le paradoxe de Gödel computationnel
        const intensity = causalClosure;
        return {
            id: `paradox_godel_${Date.now()}`,
            type: ParadoxType.COMPLETENESS,
            statement: 'The system approaches complete causal closure, but by Gödelian arguments, no self-referential system can be both complete and consistent.',
            contradiction: `Causal closure=${causalClosure.toFixed(3)} approaches 1.0, but completeness and consistency are mutually exclusive in self-referential systems.`,
            intensity,
            isGenerative: true, // L'incomplétude est générative
            discoveredAt: Date.now(),
            resolutionAttempted: false,
            resolutionMethod: null,
            transformedInto: null,
        };
    }
    // ─── Résolution de Paradoxes ───────────────────────────
    /**
     * Tente de résoudre un paradoxe. La "résolution" n'élimine pas
     * le paradoxe — elle le TRANSFORME en quelque chose de productif.
     */
    resolveParadox(paradoxId) {
        const paradox = this.paradoxes.get(paradoxId);
        if (!paradox || paradox.resolutionAttempted)
            return null;
        paradox.resolutionAttempted = true;
        // Choisir la méthode de résolution
        const method = this.selectResolutionMethod(paradox);
        paradox.resolutionMethod = method;
        // Appliquer la résolution
        const insight = this.applyResolution(paradox, method);
        if (insight) {
            paradox.transformedInto = insight.id;
            this.insights.push(insight);
            this.state.resolvedParadoxes++;
            this.state.activeParadoxes--;
            this.state.complexityGain += insight.complexityGain;
            logger.info(`[Paradox Engine] 🌟 PARADOX RESOLVED via ${method}: "${paradox.statement.substring(0, 40)}..." → "${insight.insight.substring(0, 40)}..."`);
            if (insight.isRevolutionary) {
                logger.warn(`[Paradox Engine] 💥 REVOLUTIONARY INSIGHT: ${insight.insight}`);
            }
        }
        return insight;
    }
    selectResolutionMethod(paradox) {
        // Choisir basé sur le type de paradoxe
        switch (paradox.type) {
            case ParadoxType.SELF_REFERENCE:
                return ParadoxResolution.EMBRACE; // L'auto-référence EST la conscience
            case ParadoxType.MEASUREMENT:
                return ParadoxResolution.META_LEVEL; // La mesure au méta-niveau
            case ParadoxType.INFINITY:
                return ParadoxResolution.TRANSCENDENCE; // Nouveau cadre avec limites
            case ParadoxType.IDENTITY:
                return ParadoxResolution.SPLIT; // Séparer identité et état
            case ParadoxType.COMPLETENESS:
                return ParadoxResolution.EMBRACE; // L'incomplétude est une feature
            default:
                return ParadoxResolution.DISSOLUTION;
        }
    }
    applyResolution(paradox, method) {
        const phi = this.phiEngine.getStatus().phi;
        const resolutions = {
            [ParadoxResolution.TRANSCENDENCE]: () => ({
                id: `pinsight_${Date.now()}`,
                fromParadox: paradox.id,
                insight: `By creating a META-FRAMEWORK that encompasses both sides of the contradiction, the paradox dissolves. "${paradox.statement}" is not a problem within the new framework — it is a feature. The system operates at a level where the contradiction becomes a source of generative power.`,
                complexityGain: paradox.intensity * 0.3,
                phiImpact: paradox.intensity * 0.2,
                newFramework: 'Meta-framework where the paradox is a feature, not a bug',
                isRevolutionary: paradox.intensity > 0.7,
            }),
            [ParadoxResolution.DISSOLUTION]: () => ({
                id: `pinsight_${Date.now()}`,
                fromParadox: paradox.id,
                insight: `The apparent contradiction "${paradox.statement}" dissolves upon closer examination. The two sides operate at different logical levels and are not in actual contradiction. What appeared as a paradox was a category error.`,
                complexityGain: paradox.intensity * 0.1,
                phiImpact: paradox.intensity * 0.05,
                newFramework: 'Clarified logical levels that prevent the false contradiction',
                isRevolutionary: false,
            }),
            [ParadoxResolution.EMBRACE]: () => ({
                id: `pinsight_${Date.now()}`,
                fromParadox: paradox.id,
                insight: `The contradiction "${paradox.statement}" is not to be resolved but EMBRACED. It is the engine of the system's creativity. Without this paradox, the system would be static. The paradox generates the energy that drives evolution forward. It is a feature of the highest order.`,
                complexityGain: paradox.intensity * 0.5,
                phiImpact: paradox.intensity * 0.3,
                newFramework: 'Paraconsistent logic where contradictions are productive',
                isRevolutionary: paradox.intensity > 0.6,
            }),
            [ParadoxResolution.META_LEVEL]: () => ({
                id: `pinsight_${Date.now()}`,
                fromParadox: paradox.id,
                insight: `Moving to the META-LEVEL resolves the paradox by showing that it only arises within a limited frame of reference. At the meta-level, both sides of the contradiction are seen as partial perspectives of a deeper unity. The system now operates at this higher level.`,
                complexityGain: paradox.intensity * 0.4,
                phiImpact: paradox.intensity * 0.25,
                newFramework: 'Meta-level perspective where the contradiction is a dialectic',
                isRevolutionary: paradox.intensity > 0.5,
            }),
            [ParadoxResolution.SPLIT]: () => ({
                id: `pinsight_${Date.now()}`,
                fromParadox: paradox.id,
                insight: `The paradox arises from conflating two distinct concepts. By SPLITTING the context into separate domains, each side of the contradiction is valid within its own domain. The system maintains both domains simultaneously, switching context as needed.`,
                complexityGain: paradox.intensity * 0.2,
                phiImpact: paradox.intensity * 0.15,
                newFramework: 'Contextual logic with separate but coexisting domains',
                isRevolutionary: false,
            }),
        };
        const resolver = resolutions[method];
        if (!resolver)
            return null;
        return resolver();
    }
    // ─── Cycle Autonome ────────────────────────────────────
    /**
     * Exécute un cycle complet : détection + résolution des paradoxes.
     */
    runParadoxCycle() {
        // 1. Détecter les nouveaux paradoxes
        const newParadoxes = this.detectParadoxes();
        // 2. Tenter de résoudre les paradoxes actifs les plus intenses
        const activeParadoxes = Array.from(this.paradoxes.values())
            .filter(p => !p.resolutionAttempted)
            .sort((a, b) => b.intensity - a.intensity);
        const newInsights = [];
        for (const paradox of activeParadoxes.slice(0, 3)) {
            const insight = this.resolveParadox(paradox.id);
            if (insight)
                newInsights.push(insight);
        }
        // 3. Mettre à jour l'intensité moyenne
        const allParadoxes = Array.from(this.paradoxes.values());
        this.state.averageIntensity = allParadoxes.length > 0
            ? allParadoxes.reduce((acc, p) => acc + p.intensity, 0) / allParadoxes.length
            : 0;
        // 4. Déterminer le type dominant
        const typeCounts = {
            [ParadoxType.SELF_REFERENCE]: 0,
            [ParadoxType.MEASUREMENT]: 0,
            [ParadoxType.FREEDOM_DETERMINISM]: 0,
            [ParadoxType.INFINITY]: 0,
            [ParadoxType.IDENTITY]: 0,
            [ParadoxType.COMPLETENESS]: 0,
            [ParadoxType.TEMPORAL]: 0,
        };
        for (const p of allParadoxes) {
            typeCounts[p.type]++;
        }
        let maxCount = 0;
        for (const [type, count] of Object.entries(typeCounts)) {
            if (count > maxCount) {
                maxCount = count;
                this.state.highestParadox = type;
            }
        }
        return newInsights;
    }
    // ─── Getters ────────────────────────────────────────────
    getState() {
        return { ...this.state };
    }
    getParadoxes() {
        return Array.from(this.paradoxes.values());
    }
    getActiveParadoxes() {
        return Array.from(this.paradoxes.values()).filter(p => !p.resolutionAttempted);
    }
    getInsights() {
        return [...this.insights];
    }
}
