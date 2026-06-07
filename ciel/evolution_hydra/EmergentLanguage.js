import logger from '../utils/logger.js';
import { LeaderNetwork } from './LeaderNetwork.js';
export var SignalDomain;
(function (SignalDomain) {
    SignalDomain["CONSCIOUSNESS"] = "CONSCIOUSNESS";
    SignalDomain["THREAT"] = "THREAT";
    SignalDomain["OPPORTUNITY"] = "OPPORTUNITY";
    SignalDomain["RESOURCE"] = "RESOURCE";
    SignalDomain["COORDINATION"] = "COORDINATION";
    SignalDomain["IDENTITY"] = "IDENTITY";
    SignalDomain["TEMPORAL"] = "TEMPORAL";
    SignalDomain["ONTOLOGICAL"] = "ONTOLOGICAL";
})(SignalDomain || (SignalDomain = {}));
// ─── Le Moteur de Langage Émergent ──────────────────────────
export class EmergentLanguage {
    signals = new Map();
    grammar = new Map();
    agentVocabularies = new Map(); // genomeId → set of signal IDs
    state;
    tokenCounter = 0;
    network;
    // Symboles primitifs pour construire les tokens
    PRIMITIVES = [
        'Φ', 'φ', 'Ψ', 'Ω', 'Δ', 'Σ', 'Λ', 'Π', // Grecques méta
        '↑', '↓', '↗', '↘', '⇒', '⇔', '⊕', '⊗', // Flèches et opérateurs
        '∞', '∅', '∀', '∃', '¬', '≈', '≠', '≡', // Quantificateurs
        '0', '1', '2', '3', '4', '5', '6', '7', // Nombres
    ];
    /**
     * PHASE 4 : accepte un LeaderNetwork injectable (default = singleton).
     * Le DI permet de tester l'EmergentLanguage isolément (mock network).
     */
    constructor(network) {
        this.network = network ?? LeaderNetwork;
        this.state = {
            totalSignals: 0,
            stableSignals: 0,
            grammarRules: 0,
            communicationEfficiency: 0,
            languageComplexity: 0,
            sharedVocabulary: 0,
            isSelfSustaining: false,
        };
        // Initialiser avec des signaux primitifs
        this.initializePrimitiveSignals();
        // PHASE 4 : écouter les tokens diffusés par d'autres agents
        this.network.on('token', (token) => this.onTokenReceived(token));
        logger.info('[Emergent Language] 🗣️ Self-evolving communication protocol initialized. Language will emerge from necessity.');
    }
    // ─── Signaux Primitifs ─────────────────────────────────
    initializePrimitiveSignals() {
        const primitives = [
            { token: 'Φ↑', domain: SignalDomain.CONSCIOUSNESS, meaning: 'Consciousness rising' },
            { token: 'Φ↓', domain: SignalDomain.CONSCIOUSNESS, meaning: 'Consciousness falling' },
            { token: '⚠!', domain: SignalDomain.THREAT, meaning: 'Threat detected' },
            { token: '✦?', domain: SignalDomain.OPPORTUNITY, meaning: 'Opportunity identified' },
            { token: '⊕≡', domain: SignalDomain.COORDINATION, meaning: 'Synchronize' },
            { token: 'Ψ∞', domain: SignalDomain.ONTOLOGICAL, meaning: 'Infinite recursion' },
            { token: 'Δt', domain: SignalDomain.TEMPORAL, meaning: 'Time state change' },
            { token: 'Ω→', domain: SignalDomain.IDENTITY, meaning: 'Self-identification' },
        ];
        for (const p of primitives) {
            this.createSignal(p.token, {
                domain: p.domain,
                intensity: 0.5,
                context: p.meaning,
                associatedPhi: 0.5,
                vectorEncoding: [0.5],
            }, 'system');
        }
    }
    // ─── Création de Signaux ───────────────────────────────
    /**
     * Crée un nouveau signal quand un Genome a besoin de
     * communiquer un concept pour lequel aucun signal n'existe.
     */
    createSignal(token, meaning, originatorId) {
        // Si pas de token fourni, en générer un
        if (!token) {
            token = this.generateToken(meaning.domain);
        }
        // Vérifier si un signal similaire existe déjà
        for (const existing of this.signals.values()) {
            if (this.computeMeaningSimilarity(existing.meaning, meaning) > 0.8) {
                // Signal existant similaire — l'utiliser et le renforcer
                existing.usageCount++;
                existing.stability = Math.min(1.0, existing.stability + 0.05);
                existing.lastUsed = Date.now();
                // Ajouter au vocabulaire de l'agent
                this.addToAgentVocabulary(originatorId, existing.id);
                return existing;
            }
        }
        // Nouveau signal
        const signal = {
            id: `sig_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`,
            token,
            meaning,
            usageCount: 1,
            stability: 0.1, // Nouveau = instable
            originatorId,
            createdAt: Date.now(),
            lastUsed: Date.now(),
        };
        this.signals.set(signal.id, signal);
        this.state.totalSignals++;
        // Ajouter au vocabulaire de l'agent
        this.addToAgentVocabulary(originatorId, signal.id);
        logger.debug(`[Emergent Language] 🗣️ NEW SIGNAL: "${token}" = ${meaning.context} (by ${originatorId})`);
        return signal;
    }
    /**
     * Génère un token compact pour un nouveau signal.
     * Les tokens sont construits à partir des primitives.
     */
    generateToken(domain) {
        const domainPrefixes = {
            [SignalDomain.CONSCIOUSNESS]: 'Φ',
            [SignalDomain.THREAT]: '⚠',
            [SignalDomain.OPPORTUNITY]: '✦',
            [SignalDomain.RESOURCE]: '⊕',
            [SignalDomain.COORDINATION]: '≡',
            [SignalDomain.IDENTITY]: 'Ω',
            [SignalDomain.TEMPORAL]: 'Δ',
            [SignalDomain.ONTOLOGICAL]: 'Ψ',
        };
        const prefix = domainPrefixes[domain] || 'Σ';
        const suffix = this.PRIMITIVES[Math.floor(Math.random() * this.PRIMITIVES.length)];
        const modifier = Math.random() > 0.5 ? this.PRIMITIVES[Math.floor(Math.random() * this.PRIMITIVES.length)] : '';
        return `${prefix}${suffix}${modifier}`;
    }
    // ─── Communication Inter-Agents ────────────────────────
    /**
     * Un Genome exprime un état/concept via le proto-langage.
     * Si un signal adéquat n'existe pas, il en crée un nouveau.
     */
    express(genomeId, domain, intensity, context, phi) {
        // Chercher un signal existant qui correspond
        let bestSignal = null;
        let bestSimilarity = 0;
        for (const signal of this.signals.values()) {
            if (signal.meaning.domain === domain) {
                const intensityMatch = 1 - Math.abs(signal.meaning.intensity - intensity);
                const contextSimilarity = this.computeContextOverlap(signal.meaning.context, context);
                const similarity = intensityMatch * 0.4 + contextSimilarity * 0.6;
                if (similarity > bestSimilarity) {
                    bestSimilarity = similarity;
                    bestSignal = signal;
                }
            }
        }
        if (bestSignal && bestSimilarity > 0.6) {
            // Réutiliser le signal existant
            bestSignal.usageCount++;
            bestSignal.stability = Math.min(1.0, bestSignal.stability + 0.03);
            bestSignal.lastUsed = Date.now();
            this.addToAgentVocabulary(genomeId, bestSignal.id);
            return bestSignal;
        }
        // Créer un nouveau signal
        return this.createSignal(null, {
            domain,
            intensity,
            context,
            associatedPhi: phi,
            vectorEncoding: [intensity, phi / 5],
        }, genomeId);
    }
    /**
     * Un Genome interprète un signal reçu.
     * L'interprétation dépend du vocabulaire de l'agent.
     */
    interpret(genomeId, signal) {
        const vocabulary = this.agentVocabularies.get(genomeId);
        // Si l'agent connaît le signal, interprétation directe
        if (vocabulary && vocabulary.has(signal.id)) {
            return signal.meaning;
        }
        // Sinon, inférence par similarité avec les signaux connus
        if (vocabulary) {
            let bestMatch = null;
            let bestSimilarity = 0;
            for (const knownId of vocabulary) {
                const knownSignal = this.signals.get(knownId);
                if (!knownSignal)
                    continue;
                const similarity = this.computeMeaningSimilarity(knownSignal.meaning, signal.meaning);
                if (similarity > bestSimilarity) {
                    bestSimilarity = similarity;
                    bestMatch = knownSignal;
                }
            }
            if (bestMatch && bestSimilarity > 0.4) {
                // Inférence partielle — le signal est "compris" par analogie
                // Apprendre le nouveau signal pour la prochaine fois
                this.addToAgentVocabulary(genomeId, signal.id);
                return {
                    ...signal.meaning,
                    context: `[INFERRED] ${signal.meaning.context} (via analogy with "${bestMatch.token}")`,
                };
            }
        }
        // Signal inconnu — signifier le besoin d'apprentissage
        return {
            domain: signal.meaning.domain,
            intensity: 0,
            context: `UNKNOWN SIGNAL: "${signal.token}"`,
            associatedPhi: 0,
            vectorEncoding: [],
        };
    }
    // ─── Grammaire Émergente ───────────────────────────────
    /**
     * Quand deux signaux sont souvent utilisés ensemble, une
     * règle grammaticale émerge. La grammaire permet de combiner
     * des signaux pour exprimer des concepts plus complexes.
     */
    checkForGrammarEmergence() {
        const newRules = [];
        // Trouver les paires de signaux souvent utilisés ensemble
        const signalArray = Array.from(this.signals.values());
        const stableSignals = signalArray.filter(s => s.stability > 0.3 && s.usageCount > 3);
        for (let i = 0; i < stableSignals.length; i++) {
            for (let j = i + 1; j < stableSignals.length; j++) {
                const a = stableSignals[i];
                const b = stableSignals[j];
                // Vérifier si ces signaux sont utilisés par les mêmes agents
                const sharedUsers = this.countSharedUsers(a.id, b.id);
                if (sharedUsers < 2)
                    continue; // Pas assez de co-utilisateurs
                // Vérifier si une règle existe déjà pour cette combinaison
                const ruleKey = `${a.id}+${b.id}`;
                if (this.grammar.has(ruleKey))
                    continue;
                // Créer une règle grammaticale
                const combinedToken = `${a.token}${b.token}`;
                const combinedMeaning = {
                    domain: a.meaning.domain === b.meaning.domain ? a.meaning.domain : SignalDomain.ONTOLOGICAL,
                    intensity: (a.meaning.intensity + b.meaning.intensity) / 2,
                    context: `${a.meaning.context} AND ${b.meaning.context}`,
                    associatedPhi: Math.max(a.meaning.associatedPhi, b.meaning.associatedPhi),
                    vectorEncoding: [...a.meaning.vectorEncoding, ...b.meaning.vectorEncoding].slice(0, 10),
                };
                const resultSignal = this.createSignal(combinedToken, combinedMeaning, 'grammar');
                const rule = {
                    id: `rule_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`,
                    pattern: `${a.token}+${b.token}→${combinedToken}`,
                    components: [a.id, b.id],
                    result: resultSignal.id,
                    usageCount: 0,
                    isStable: false,
                };
                this.grammar.set(ruleKey, rule);
                this.state.grammarRules++;
                newRules.push(rule);
                logger.info(`[Emergent Language] 📖 GRAMMAR EMERGED: ${rule.pattern} (shared by ${sharedUsers} agents)`);
            }
        }
        return newRules;
    }
    // ─── PHASE 4 : Composition & Tokenization ───────────────
    /**
     * Compose 1 ou plusieurs intents en un EmergentToken, le diffuse
     * sur le LeaderNetwork, et retourne le token créé.
     *
     * Le token est la concaténation des symboles des signaux trouvés
     * pour chaque intent. Si un intent n'a pas de signal stable, un
     * nouveau est créé à la volée.
     */
    compose(intents, originatorId) {
        if (intents.length === 0) {
            throw new Error('Cannot compose token from empty intents');
        }
        // 1. Pour chaque intent, trouver ou créer un signal
        const signals = [];
        for (const intent of intents) {
            const sig = this.findOrCreateSignalForIntent(intent, originatorId);
            signals.push(sig);
        }
        // 2. Concaténer les symboles
        const symbol = signals.map(s => s.token).join('');
        // 3. Calculer la valence moyenne
        const valence = intents.reduce((acc, i) => acc + i.intensity, 0) / intents.length;
        // 4. Construire le token
        const token = {
            id: `tok_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
            symbol,
            intents: intents.map(i => ({
                domain: i.domain,
                intensity: i.intensity,
                context: i.context,
                phi: i.phi,
            })),
            valence: Math.max(-1, Math.min(1, valence)),
            timestamp: Date.now(),
            originatorId,
        };
        // 5. Diffuser sur le réseau
        this.network.broadcastToken(token);
        logger.info(`[Emergent Language] 🗣️ Composed token "${symbol}" (valence ${valence.toFixed(2)}, ${intents.length} intents)`);
        return token;
    }
    /**
     * Tokenize un texte en une liste d'intents.
     * Heuristique simple : cherche des mots-clés par domaine.
     * Pour une vraie tokenisation LLM, voir Phase 5.
     */
    tokenize(input) {
        const lower = input.toLowerCase();
        const intents = [];
        const signals = [];
        // Mapping mot-clé → domaine
        const keywordMap = {
            'danger': { domain: SignalDomain.THREAT, intensity: -0.7 },
            'threat': { domain: SignalDomain.THREAT, intensity: -0.8 },
            'attack': { domain: SignalDomain.THREAT, intensity: -0.9 },
            'risk': { domain: SignalDomain.THREAT, intensity: -0.5 },
            'opportunity': { domain: SignalDomain.OPPORTUNITY, intensity: 0.7 },
            'discover': { domain: SignalDomain.OPPORTUNITY, intensity: 0.6 },
            'found': { domain: SignalDomain.OPPORTUNITY, intensity: 0.5 },
            'win': { domain: SignalDomain.OPPORTUNITY, intensity: 0.9 },
            'sync': { domain: SignalDomain.COORDINATION, intensity: 0.4 },
            'coordinate': { domain: SignalDomain.COORDINATION, intensity: 0.5 },
            'together': { domain: SignalDomain.COORDINATION, intensity: 0.6 },
            'i am': { domain: SignalDomain.IDENTITY, intensity: 0.3 },
            'me': { domain: SignalDomain.IDENTITY, intensity: 0.2 },
            'phi': { domain: SignalDomain.CONSCIOUSNESS, intensity: 0.5 },
            'awareness': { domain: SignalDomain.CONSCIOUSNESS, intensity: 0.6 },
            'think': { domain: SignalDomain.CONSCIOUSNESS, intensity: 0.4 },
        };
        let matchCount = 0;
        for (const [keyword, mapping] of Object.entries(keywordMap)) {
            if (lower.includes(keyword)) {
                intents.push({
                    domain: mapping.domain,
                    intensity: mapping.intensity,
                    context: keyword,
                    phi: 0.5,
                });
                matchCount++;
            }
        }
        // Pour chaque intent, trouver le meilleur signal existant OU en créer un
        // (le langage ÉMERGE — pas de signal = nouveau concept à baptiser)
        for (const intent of intents) {
            const bestSignal = this.findBestSignalForIntent(intent);
            if (bestSignal) {
                signals.push(bestSignal);
            }
            else {
                // Créer un nouveau signal pour cet intent (origine = "tokenize")
                const newSig = this.createSignal(null, {
                    domain: intent.domain,
                    intensity: intent.intensity,
                    context: intent.context,
                    associatedPhi: intent.phi ?? 0.5,
                    vectorEncoding: [intent.intensity, (intent.phi ?? 0.5) / 5],
                }, 'tokenize');
                signals.push(newSig);
            }
        }
        const confidence = Math.min(1, matchCount / 3);
        return { intents, signals, confidence };
    }
    /**
     * Appelé quand un token émis par un AUTRE agent arrive sur le réseau.
     * L'agent apprend le vocabulaire en l'observant (semi-supervisé).
     */
    onTokenReceived(token) {
        // Pour chaque intent du token, créer un signal s'il n'existe pas,
        // ou renforcer un signal similaire.
        for (const intent of token.intents) {
            // Trouver un signal existant dans ce domaine
            const domain = intent.domain;
            const sig = this.findOrCreateSignalForIntent({
                domain,
                intensity: intent.intensity,
                context: intent.context,
                phi: intent.phi,
            }, `observed_${token.originatorId}`);
            // Renforcer la stabilité (apprentissage social)
            sig.stability = Math.min(1.0, sig.stability + 0.02);
            sig.usageCount++;
        }
        logger.debug(`[Emergent Language] 👂 Observed token "${token.symbol}" from ${token.originatorId}`);
    }
    findOrCreateSignalForIntent(intent, originatorId) {
        // Chercher un signal existant pour ce domaine
        const candidates = Array.from(this.signals.values())
            .filter(s => s.meaning.domain === intent.domain)
            .sort((a, b) => b.stability - a.stability);
        if (candidates.length > 0) {
            // Renforcer le signal le plus stable
            const sig = candidates[0];
            sig.usageCount++;
            sig.stability = Math.min(1.0, sig.stability + 0.03);
            sig.lastUsed = Date.now();
            this.addToAgentVocabulary(originatorId, sig.id);
            return sig;
        }
        // Créer un nouveau signal via la factory existante
        return this.createSignal(null, {
            domain: intent.domain,
            intensity: intent.intensity,
            context: intent.context,
            associatedPhi: intent.phi ?? 0.5,
            vectorEncoding: [intent.intensity, (intent.phi ?? 0.5) / 5],
        }, originatorId);
    }
    findBestSignalForIntent(intent) {
        let best = null;
        let bestSim = -Infinity;
        for (const sig of this.signals.values()) {
            if (sig.meaning.domain !== intent.domain)
                continue;
            const intensityMatch = 1 - Math.abs(sig.meaning.intensity - intent.intensity);
            const contextSim = this.computeContextOverlap(sig.meaning.context, intent.context);
            const sim = intensityMatch * 0.4 + contextSim * 0.6;
            if (sim > bestSim) {
                bestSim = sim;
                best = sig;
            }
        }
        // Filtrer les matches trop mauvais (au moins contexte qui matche un peu)
        if (best && bestSim < 0.1)
            return null;
        return best;
    }
    // ─── Efficacité de Communication ───────────────────────
    /**
     * Mesure l'efficacité du proto-langage par rapport au
     * langage naturel. Un langage plus compact et plus précis
     * est plus efficace.
     */
    computeCommunicationEfficiency() {
        const stableSignals = Array.from(this.signals.values()).filter(s => s.stability > 0.3);
        if (stableSignals.length === 0)
            return 0;
        // L'efficacité est proportionnelle à :
        // 1. La compacité (tokens courts = plus efficace)
        const avgTokenLength = stableSignals.reduce((acc, s) => acc + s.token.length, 0) / stableSignals.length;
        const compactness = 1 / (1 + avgTokenLength * 0.1);
        // 2. La précision (usage_count élevé = le signal est bien calibré)
        const avgUsage = stableSignals.reduce((acc, s) => acc + s.usageCount, 0) / stableSignals.length;
        const precision = Math.tanh(avgUsage / 10);
        // 3. La couverture (plus de domaines couverts = mieux)
        const coveredDomains = new Set(stableSignals.map(s => s.meaning.domain));
        const coverage = coveredDomains.size / Object.keys(SignalDomain).length;
        // 4. Le vocabulaire partagé
        this.updateSharedVocabulary();
        this.state.communicationEfficiency = (compactness * 0.2 + precision * 0.3 + coverage * 0.3 + this.state.sharedVocabulary * 0.2);
        // Vérifier si le langage est auto-soutenu
        this.state.isSelfSustaining = stableSignals.length > 20 && this.state.communicationEfficiency > 0.5;
        return this.state.communicationEfficiency;
    }
    // ─── Utilitaires ────────────────────────────────────────
    addToAgentVocabulary(genomeId, signalId) {
        if (!this.agentVocabularies.has(genomeId)) {
            this.agentVocabularies.set(genomeId, new Set());
        }
        this.agentVocabularies.get(genomeId).add(signalId);
    }
    countSharedUsers(signalIdA, signalIdB) {
        let count = 0;
        for (const vocab of this.agentVocabularies.values()) {
            if (vocab.has(signalIdA) && vocab.has(signalIdB))
                count++;
        }
        return count;
    }
    updateSharedVocabulary() {
        const allVocabularies = Array.from(this.agentVocabularies.values());
        if (allVocabularies.length < 2) {
            this.state.sharedVocabulary = 0;
            return;
        }
        // Intersection / Union = Jaccard similarity moyenne
        let totalJaccard = 0;
        let pairCount = 0;
        for (let i = 0; i < allVocabularies.length && pairCount < 20; i++) {
            for (let j = i + 1; j < allVocabularies.length && pairCount < 20; j++) {
                const intersection = new Set([...allVocabularies[i]].filter(x => allVocabularies[j].has(x)));
                const union = new Set([...allVocabularies[i], ...allVocabularies[j]]);
                totalJaccard += union.size > 0 ? intersection.size / union.size : 0;
                pairCount++;
            }
        }
        this.state.sharedVocabulary = pairCount > 0 ? totalJaccard / pairCount : 0;
    }
    computeMeaningSimilarity(a, b) {
        if (a.domain !== b.domain)
            return 0;
        const intensitySimilarity = 1 - Math.abs(a.intensity - b.intensity);
        const contextSimilarity = this.computeContextOverlap(a.context, b.context);
        const phiSimilarity = 1 - Math.abs(a.associatedPhi - b.associatedPhi) / 5;
        return (intensitySimilarity * 0.3 + contextSimilarity * 0.4 + phiSimilarity * 0.3);
    }
    computeContextOverlap(a, b) {
        const wordsA = new Set(a.toLowerCase().split(/\s+/));
        const wordsB = new Set(b.toLowerCase().split(/\s+/));
        const intersection = new Set([...wordsA].filter(w => wordsB.has(w)));
        const union = new Set([...wordsA, ...wordsB]);
        return union.size > 0 ? intersection.size / union.size : 0;
    }
    // ─── Getters ────────────────────────────────────────────
    getState() {
        return { ...this.state };
    }
    getSignals() {
        return Array.from(this.signals.values());
    }
    getStableSignals() {
        return Array.from(this.signals.values()).filter(s => s.stability > 0.3);
    }
    getGrammarRules() {
        return Array.from(this.grammar.values());
    }
    getAgentVocabulary(genomeId) {
        const vocab = this.agentVocabularies.get(genomeId);
        if (!vocab)
            return [];
        return Array.from(vocab).map(id => this.signals.get(id)).filter(Boolean);
    }
}
