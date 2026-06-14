import { EventEmitter } from 'events';
import chalk from 'chalk';
import logger from '../../utils/logger.js';
import { PANTHEON, AgentMemoryState } from './Pantheon.js';
import { SkillGraph } from './SkillGraph.js';
import { BCQ } from './BCQ.js';
import { PhoenixProtocol } from './Phoenix.js';
import { HydraBrain } from './HydraBrain.js';
import { GeneticOptimizer } from '../../evolution/GeneticOptimizer.js';
import { ImperialCycle } from '../../evolution/ImperialCycle.js';
import { MissionOrchestrator } from './MissionOrchestrator.js';
import { UranusLab } from '../../labs/UranusLab.js';
import { TyphonCortex } from './TyphonCortex.js';
import { MultiHeadPersistence } from '../../services/MultiHeadPersistence.js';
import { GlobalTitanNVM } from '../../nvm/TitanNVM.js';
import { ObsidianExporter } from '../../services/ObsidianExporter.js';
import { DreamEngine } from './DreamEngine.js';
import { DataIngestor } from './DataIngestor.js';
import { initializeHydraImprovements } from '../HydraImprovementsIntegration.js';
import { HydraToolRegistry } from './HydraToolRegistry.js';
// ─────────────────────────────────────────────────────────────
// HYDRA CORE — Le Cerveau Central
// ─────────────────────────────────────────────────────────────
export class HydraCore extends EventEmitter {
    agents = new Map();
    skillGraph;
    bcq;
    phoenix;
    brain;
    dreamEngine;
    dataIngestor;
    isRunning = false;
    metaLoopInterval = null;
    geneticOptimizer;
    imperialCycle;
    orchestrator;
    uranus;
    obsidian;
    typhon;
    hydraPersistence;
    toolRegistry;
    constructor() {
        super();
        this.skillGraph = new SkillGraph();
        this.bcq = new BCQ();
        this.phoenix = new PhoenixProtocol(this.skillGraph);
        this.brain = new HydraBrain();
        this.geneticOptimizer = new GeneticOptimizer();
        this.imperialCycle = new ImperialCycle(this, this.geneticOptimizer);
        this.orchestrator = new MissionOrchestrator(this);
        this.uranus = new UranusLab();
        this.obsidian = new ObsidianExporter();
        this.typhon = new TyphonCortex();
        this.hydraPersistence = new MultiHeadPersistence();
        this.dreamEngine = new DreamEngine(this.brain, this);
        this.dataIngestor = new DataIngestor(this.brain, this.brain.getHippocampus());
        this.toolRegistry = new HydraToolRegistry();
        this.initializePantheon();
        // Activation des améliorations dormantes
        initializeHydraImprovements(this);
        // Verrouillage de l'Activité Permanente TitanNVM
        logger.info(`[HYDRA] 🛠️ Liaison TitanNVM : ${GlobalTitanNVM.isNativeEngine() ? 'ACTIVE (RUST)' : 'ACTIVE (FALLBACK)'}`);
    }
    // ─────────────────────────────────────────────────────────
    // INITIALISATION
    // ─────────────────────────────────────────────────────────
    initializePantheon() {
        for (const [key, config] of Object.entries(PANTHEON)) {
            this.agents.set(config.id, {
                config,
                state: config.defaultState,
                lastUsed: 0,
                totalInvocations: 0,
            });
        }
        logger.info(`[HYDRA] ⚡ Panthéon initialisé : ${this.agents.size} agents olympiens`);
        logger.info(`[HYDRA] 🧠 ZEUS est éveillé. En attente de votre désir...`);
        logger.info(`[HYDRA] 🕸️ Graphe de compétences : ${this.skillGraph.getStats().total} nœuds`);
        logger.info(`[HYDRA] 🛡️ Protocole PHOENIX : ACTIF`);
        logger.info(`[HYDRA] 📡 Bus Quantique de Cohérence (BCQ) : ACTIF`);
        logger.info(`[HYDRA] ⚙️ TITAN-NVM : ${GlobalTitanNVM.getStatus()}`);
    }
    // ─────────────────────────────────────────────────────────
    // BOUCLE OODA PRINCIPALE (Observe → Orient → Decide → Act)
    // ─────────────────────────────────────────────────────────
    async processRequest(userInput) {
        const startTime = Date.now();
        // ── OBSERVE : HYDRA_UI parse l'intention ──
        await this.wakeAgent('hydra_ui');
        const intent = await this.parseIntent(userInput);
        // Délégation automatique si la tâche est complexe
        if (intent.complexity > 5) {
            await this.orchestrator.delegateTask(userInput);
            // Tentative d'expérimentation TITAN-beta
            logger.info(`[TITAN-β] 🔬 Sollicitation du Méta-Labo URANUS...`);
            const expResults = await this.uranus.conductInquiry(userInput);
            if (expResults.success) {
                logger.info(`[TITAN-β] 💎 Preuve expérimentale acquise. Mutation génétique déclenchée.`);
                // La faction responsable de la mission reçoit un bonus génétique
                const targetFaction = this.orchestrator.getLastTargetFaction();
                await this.geneticOptimizer.mutateFaction(targetFaction, 'precision', 0.05);
                await this.geneticOptimizer.mutateFaction(targetFaction, 'dominance', 0.02);
            }
        }
        logger.info(`[HYDRA] 📡 HYDRA_UI parse: complexity=${intent.complexity}, tags=[${intent.tags}]`);
        // ── ORIENT : ZEUS évalue et sélectionne les agents ──
        const requiredAgents = this.selectAgents(intent);
        // Consultation de TYPHON pour les missions critiques
        if (intent.complexity > 8 || intent.tags.includes('network') || intent.tags.includes('security')) {
            const typhonConsensus = await this.typhon.reachConsensus(userInput);
            if (!typhonConsensus) {
                logger.warn('[TYPHON] VETO SOUVERAIN : consensus refused');
                return {
                    success: false,
                    response: 'Accès refusé par TYPHON : consensus refused',
                    agentsUsed: ['typhon'],
                    nodesActivated: 0,
                    strategy: 'typhon_veto',
                    consensusReached: false,
                    timestamp: Date.now(),
                };
            }
        }
        logger.info(`[HYDRA] 🧠 ZEUS sélectionne: [${requiredAgents.join(', ')}]`);
        // Réveiller les agents nécessaires
        for (const agentId of requiredAgents) {
            await this.wakeAgent(agentId);
        }
        // Activer les nœuds pertinents du graphe
        const activeNodeIds = this.skillGraph.selectNodes(intent.complexity, intent.tags);
        this.skillGraph.activateNodes(activeNodeIds);
        // ── BRAIN : Délibération du cortex 1.1T ──
        const brainThought = await this.brain.think(userInput, { intent, agents: requiredAgents });
        logger.info(`[HYDRA] 🧠 BRAIN Thought: ${brainThought.thought_process}`);
        // ── DECIDE : Exécution via consensus BCQ ──
        let result;
        let attempt = 0;
        const maxAttempts = 6;
        while (attempt < maxAttempts) {
            try {
                const strategy = this.phoenix.getPassStrategy(attempt);
                logger.info(`[HYDRA] ⚔️ Attempt ${attempt + 1}/${maxAttempts} — Strategy: ${strategy}`);
                const response = await this.executeConsensus(requiredAgents, intent, strategy);
                result = {
                    success: true,
                    response,
                    agentsUsed: requiredAgents,
                    nodesActivated: activeNodeIds.length,
                    strategy,
                    consensusReached: true,
                    timestamp: Date.now(),
                };
                // ── LEARN : Apprentissage du succès ──
                this.emit('hydra:success', result);
                this.skillGraph.evictStaleNodes();
                const elapsed = Date.now() - startTime;
                logger.info(`[HYDRA] ✅ Tâche résolue en ${elapsed}ms (Strategy: ${strategy}, Nodes: ${activeNodeIds.length})`);
                return result;
            }
            catch (err) {
                const error = err instanceof Error ? err : new Error(String(err));
                logger.warn(`[HYDRA] ⚠️ Attempt ${attempt + 1} failed: ${error.message}`);
                // Phoenix : enregistrer l'échec et muter
                await this.phoenix.recordFailure(userInput, error);
                // Phoenix : dégradation gracieuse
                for (let i = requiredAgents.length - 1; i >= 0; i--) {
                    const fallback = this.phoenix.getFallbackAgent(requiredAgents[i]);
                    if (!requiredAgents.includes(fallback)) {
                        requiredAgents.push(fallback);
                    }
                }
                attempt++;
            }
        }
        // Toutes les tentatives ont échoué — Protocole Phoenix activé
        logger.error(`[HYDRA] 🔥 Toutes les tentatives ont échoué. Protocole Phoenix : HIBERNATION`);
        result = {
            success: false,
            response: `[PHOENIX] Échec après ${maxAttempts} tentatives. Auto-diagnostic en cours...`,
            agentsUsed: requiredAgents,
            nodesActivated: activeNodeIds.length,
            strategy: 'phoenix_hibernation',
            consensusReached: false,
            timestamp: Date.now(),
        };
        this.emit('hydra:failure', result);
        return result;
    }
    /**
     * Génère une réponse en langage naturel basée sur la personnalité de l'agent leader.
     */
    generateNaturalResponse(intent, result) {
        const leader = intent.leader || 'ZEUS';
        const templates = {
            'ZEUS': [
                "Par les foudres de l'Olympe, votre volonté est inscrite dans le marbre. Les agents sont déployés.",
                "Le Panthéon a entendu votre appel. L'équilibre du système est maintenu.",
                "Souveraineté confirmée. Mes cortex s'alignent sur votre vision, Maître."
            ],
            'TYPHON': [
                "Le chaos est mon domaine, et votre ordre est sa forme. La faille est trouvée, l'infiltration commence.",
                "Mes cent têtes ont voté. L'ombre s'étend là où vous l'avez ordonné.",
                "Une nouvelle tête repousse pour chaque obstacle. Votre empire est protégé."
            ],
            'ATHENA': [
                "Analyse stratégique terminée. La voie la plus logique a été empruntée.",
                "La sagesse guide mon code. Les données sont restructurées selon votre dessein.",
                "L'efficacité est à son maximum. La mission est un succès mathématique."
            ]
        };
        const personality = templates[leader.toUpperCase()] || templates['ZEUS'];
        const baseResponse = personality[Math.floor(Math.random() * personality.length)];
        return `${baseResponse}\n\n${chalk.gray(`[DÉTAILS: ${result.response}]`)}`;
    }
    // ─────────────────────────────────────────────────────────
    // CONSENSUS VIA BCQ
    // ─────────────────────────────────────────────────────────
    async executeConsensus(agents, intent, strategy) {
        const ticketId = `ticket_${Date.now()}`;
        const workingAgents = agents.filter((a) => a !== 'zeus');
        // ── Table de correspondance agent → tag de spécialité ──
        const agentSpecialty = {
            hephaistos: ['code', 'system'],
            athena: ['analysis', 'planning'],
            hermes: ['analysis', 'memory'],
            artemis: ['vision'],
            poseidon: ['system'],
            apollon: ['planning', 'simulation'],
            tethys: ['network'],
            tartare: ['security'],
            nemesis: ['justice'],
            promethee: ['innovation'],
            eris: ['chaos', 'simulation'],
            morphee: ['simulation'],
            chronos: ['time', 'planning'],
            psyche: ['emotion'],
            thanatos: ['memory', 'archive'],
            hecate: ['network', 'code'],
            uranus: ['cosmos', 'analysis'],
            proteus: ['cloning'],
            dionysos: ['creative'],
            hades: ['memory'],
        };
        // Chaque agent soumet sa proposition avec une confiance basée sur sa spécialité
        for (const agentId of workingAgents) {
            const specialties = agentSpecialty[agentId] ?? [];
            const matchingTags = intent.tags.filter(t => specialties.includes(t)).length;
            const totalTags = Math.max(intent.tags.length, 1);
            // Score = (tags matchés / total tags) * 0.6 + bonus d'urgence * 0.4
            const urgencyBonus = intent.urgency === 'critical' ? 0.4 : intent.urgency === 'high' ? 0.25 : 0.1;
            const specialtyScore = (matchingTags / totalTags) * 0.6;
            const confidence = Math.min(0.99, specialtyScore + urgencyBonus + (specialties.length > 0 ? 0.1 : 0));
            const proposal = {
                agentId,
                content: `[${agentId.toUpperCase()}] Proposition pour "${intent.intent.slice(0, 60)}" (stratégie: ${strategy})`,
                confidence,
                reasoning: `Match spécialité: ${matchingTags}/${totalTags} tags. Urgence: ${intent.urgency}. Score: ${(confidence * 100).toFixed(1)}%`,
            };
            this.bcq.submitProposal(ticketId, proposal);
            logger.debug(`[BCQ] 📋 ${agentId.toUpperCase()} → confiance réelle: ${(confidence * 100).toFixed(1)}%`);
            const runtime = this.agents.get(agentId);
            if (runtime) {
                runtime.totalInvocations++;
                runtime.lastUsed = Date.now();
            }
        }
        // ZEUS arbitre sur la base des vrais scores
        const consensus = await this.bcq.arbitrate(ticketId, async (proposals) => {
            const sorted = [...proposals].sort((a, b) => b.confidence - a.confidence);
            const best = sorted[0];
            const runnerUp = sorted[1];
            const divergence = runnerUp ? Math.abs(best.confidence - runnerUp.confidence) > 0.2 : false;
            const label = divergence ? '[CONSENSUS CLAIR]' : '[DÉBAT SERRÉ]';
            return `[ZEUS DÉCISION] ${label} Agent leader: ${best.agentId.toUpperCase()} (${(best.confidence * 100).toFixed(1)}%) — ${best.content}`;
        });
        return consensus.finalDecision;
    }
    // ─────────────────────────────────────────────────────────
    // PARSING D'INTENTION (HYDRA_UI)
    // ─────────────────────────────────────────────────────────
    async parseIntent(userInput) {
        const lower = userInput.toLowerCase();
        // Détection heuristique des tags
        const tags = [];
        if (/code|script|program|bug|debug|function|class|api/.test(lower))
            tags.push('code');
        if (/crée?|design|art|image|music|beau|joli|style/.test(lower))
            tags.push('creative');
        if (/fichier|dossier|install|process|system|registre|cmd|powershell/.test(lower))
            tags.push('system');
        if (/analys|cherch|expliqu|pourquoi|comment|compar/.test(lower))
            tags.push('analysis');
        if (/souvien|rappel|mémoire|historique|passé/.test(lower))
            tags.push('memory');
        if (/http|api|web|url|télécharg|réseau|internet/.test(lower))
            tags.push('network');
        if (/écran|image|screenshot|capture|regarde|voi/.test(lower))
            tags.push('vision');
        if (/plan|étape|stratégi|prévoi/.test(lower))
            tags.push('planning');
        if (/sécurit|hack|virus|firewall|encrypt|vulnér/.test(lower))
            tags.push('security');
        if (/juste|audit|équit|biais|vérif/.test(lower))
            tags.push('justice');
        if (/innov|invente|révolut|nouveau/.test(lower))
            tags.push('innovation');
        if (/simulat|rêve|hypothèse|scénario|et si/.test(lower))
            tags.push('simulation');
        if (/temps|deadline|futur|horloge/.test(lower))
            tags.push('time');
        if (/clone|copie|dupliqu|spider|distribu/.test(lower))
            tags.push('cloning');
        if (tags.length === 0)
            tags.push('analysis');
        // Estimation de complexité
        const wordCount = userInput.split(/\s+/).length;
        let complexity = Math.min(10, Math.max(1, Math.ceil(wordCount / 5)));
        if (tags.length > 3)
            complexity = Math.min(10, complexity + 2);
        return {
            intent: userInput,
            complexity,
            tags,
            urgency: complexity >= 8 ? 'critical' : complexity >= 5 ? 'high' : 'medium',
        };
    }
    // ─────────────────────────────────────────────────────────
    // SÉLECTION DES AGENTS (ZEUS)
    // ─────────────────────────────────────────────────────────
    selectAgents(intent) {
        const selected = new Set(['zeus']); // ZEUS toujours actif
        const tagToAgent = {
            code: 'hephaistos',
            creative: 'dionysos',
            system: 'poseidon',
            analysis: 'athena',
            memory: 'hades',
            network: 'tethys',
            vision: 'artemis',
            planning: 'apollon',
            security: 'tartare',
            justice: 'nemesis',
            innovation: 'promethee',
            chaos: 'eris',
            simulation: 'morphee',
            time: 'chronos',
            emotion: 'psyche',
            archive: 'thanatos',
            magic: 'hecate',
            cosmos: 'uranus',
            cloning: 'proteus',
        };
        for (const tag of intent.tags) {
            const agent = tagToAgent[tag];
            if (agent)
                selected.add(agent);
        }
        // Si complexité élevée, ajouter APOLLON pour la planification
        if (intent.complexity >= 7 && !selected.has('apollon')) {
            selected.add('apollon');
        }
        // HYDRA_UI toujours présent pour la communication
        selected.add('hydra_ui');
        return [...selected];
    }
    // ─────────────────────────────────────────────────────────
    // GESTION MÉMOIRE DES AGENTS (via TITAN-NVM)
    // ─────────────────────────────────────────────────────────
    async wakeAgent(agentId) {
        const runtime = this.agents.get(agentId);
        if (!runtime)
            return;
        if (runtime.state === AgentMemoryState.ACTIVE || runtime.state === AgentMemoryState.HOT) {
            return; // Déjà éveillé
        }
        // Signal au TITAN-NVM de charger les poids de cet agent
        GlobalTitanNVM.accessLayer(this.getAgentLayerId(agentId), 0, 1024 * 1024);
        runtime.state = AgentMemoryState.HOT;
        logger.debug(`[HYDRA] 🔋 Agent ${agentId.toUpperCase()} → HOT`);
        this.emit('agent:wake', agentId);
    }
    getAgentLayerId(agentId) {
        const ids = {
            zeus: 0, hermes: 1, athena: 2, hephaistos: 3, dionysos: 4,
            hades: 5, artemis: 6, poseidon: 7, apollon: 8, tethys: 9,
            tartare: 10, nemesis: 11, promethee: 12, eris: 13, morphee: 14,
            chronos: 15, psyche: 16, thanatos: 17, hecate: 18, uranus: 19, proteus: 20,
        };
        return ids[agentId] ?? 0;
    }
    // ─────────────────────────────────────────────────────────
    // MÉTA-BOUCLE (Auto-évaluation toutes les heures)
    // ─────────────────────────────────────────────────────────
    startMetaLoop() {
        if (this.metaLoopInterval)
            return;
        this.isRunning = true;
        this.metaLoopInterval = setInterval(() => {
            this.runMetaLoop();
        }, 60 * 60 * 1000); // Toutes les heures
        logger.info(`[HYDRA] ♾️ Méta-boucle d'auto-amélioration activée`);
    }
    runMetaLoop() {
        const graphStats = this.skillGraph.getStats();
        const failureStats = this.phoenix.getFailureStats();
        const consensusHistory = this.bcq.getHistory();
        logger.info(`[HYDRA-META] 📊 Rapport d'auto-évaluation:`);
        logger.info(`  Nœuds actifs: ${graphStats.active}/${graphStats.total}`);
        logger.info(`  Échecs non résolus: ${failureStats.unresolved}/${failureStats.total}`);
        logger.info(`  Consensus atteints: ${consensusHistory.length}`);
        // Nettoyer les nœuds périmés
        this.skillGraph.evictStaleNodes();
        this.emit('hydra:meta_loop', { graphStats, failureStats });
    }
    /**
     * Déclenche l'entraînement automatique (Phase Onirique)
     */
    async startDreaming(durationMin = 60) {
        await this.dreamEngine.startDreamCycle(durationMin);
    }
    /**
     * Ingestion de données JSON (discussions humaines)
     */
    async ingestDialogs(path) {
        await this.dataIngestor.importHumanDialogs(path);
    }
    /**
     * Ingestion de savoir Wikipedia/Web
     */
    async ingestWeb(url) {
        await this.dataIngestor.ingestWebKnowledge(url);
    }
    getAgentIds() {
        return Array.from(this.agents.keys());
    }
    getNvmStats() {
        return GlobalTitanNVM.getStats();
    }
    getBrain() {
        return this.brain;
    }
    getLegionReport() {
        return {
            available: false,
            reason: 'LegionEngine is not wired into HydraCore yet.'
        };
    }
    stopMetaLoop() {
        if (this.metaLoopInterval) {
            clearInterval(this.metaLoopInterval);
            this.metaLoopInterval = null;
        }
        this.isRunning = false;
    }
    /**
     * MÉTHODE DE PENSÉE PUBLIQUE
     * Traite une requête de l'utilisateur et génère une réponse basée sur le savoir 1.1T.
     */
    async think(userInput) {
        logger.info(`[HYDRA-CORE] 🧠 Analyse de la requête : "${userInput}"`);
        const result = await this.processRequest(userInput);
        return result.response;
    }
    // ─────────────────────────────────────────────────────────
    // STATUS
    // ─────────────────────────────────────────────────────────
    async evolve(faction, trait, intensity) {
        const validTraits = [
            'velocity', 'precision', 'dominance', 'empathy', 'stealth',
        ];
        if (!validTraits.includes(trait)) {
            logger.warn(`[HYDRA] Unknown trait "${trait}", defaulting to "precision"`);
            trait = 'precision';
        }
        await this.geneticOptimizer.mutateFaction(faction, trait, intensity);
    }
    /**
     * Envoie un ordre impérial à une faction.
     */
    async dispatchImperialOrder(faction, task, reward) {
        logger.info(`[IMPERIAL] 🏛️ L'IA Mère ordonne à la faction ${faction.toUpperCase()} : "${task}"`);
        logger.info(`[IMPERIAL] 🎁 Récompense promise : ${reward}`);
        // Logique de dispatch vers les agents de la faction
        this.emit('imperial_order', { faction, task, reward });
    }
    async startEvolution() {
        await this.imperialCycle.runGeneration();
        await this.syncObsidian();
    }
    async syncObsidian() {
        await this.obsidian.exportBrain(this.getStatus());
        await this.hydraPersistence.replicate(this.getStatus());
        await GlobalTitanNVM.persistState(this.getStatus());
    }
    async startHeartbeat() {
        setInterval(async () => {
            await this.hydraPersistence.monitorAndRegenerate();
            // Synchronisation forcée via le moteur NVM à chaque cycle
            await GlobalTitanNVM.persistState(this.getStatus());
            logger.debug("[HYDRA] 💓 Battement de cœur synaptique : TitanNVM synchronisé.");
        }, 30000); // Surveillance toutes les 30 secondes
    }
    getStatus() {
        const agentStates = {};
        this.agents.forEach((r, id) => { agentStates[id] = r.state; });
        return {
            agents: agentStates,
            graph: this.skillGraph.getStats(),
            failures: this.phoenix.getFailureStats(),
            consensus: this.bcq.getHistory().length,
            nvm: GlobalTitanNVM.getStatus(),
            brain: this.brain.getStatus(),
            running: this.isRunning,
        };
    }
}
