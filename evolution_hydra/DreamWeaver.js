import logger from '../utils/logger.js';
import { errorMessage } from '../types/index.js';
import { randomUUID } from 'crypto';
export class DreamWeaver {
    coordinator;
    karma;
    isDreaming = false;
    // Constantes de sommeil
    IDLE_THRESHOLD_MS = 60000; // 1 minute d'inactivité déclenche le sommeil
    sleepInterval = null;
    lastActivityTick = Date.now();
    constructor(coordinator, karma) {
        this.coordinator = coordinator;
        this.karma = karma;
        logger.info('[DreamWeaver] 🌙 Moteur Onirique activé. En attente de phase REM_SLEEP.');
        this.startCircadianRhythm();
    }
    /**
     * À appeler par le système lors d'une action utilisateur pour repousser le sommeil
     */
    wakeUp() {
        this.lastActivityTick = Date.now();
        if (this.isDreaming) {
            logger.info('[DreamWeaver] ☀️ Réveil brutal. Fin du rêve.');
            this.isDreaming = false;
        }
    }
    startCircadianRhythm() {
        this.sleepInterval = setInterval(() => {
            const timeSinceLastAction = Date.now() - this.lastActivityTick;
            const systemLoad = this.coordinator.getRealTimeDashboard().pendingTasks;
            // Si le système est inactif et n'a pas de tâches en attente
            if (timeSinceLastAction > this.IDLE_THRESHOLD_MS && systemLoad === 0 && !this.isDreaming) {
                this.enterREMSleep();
            }
        }, 10000);
    }
    async enterREMSleep() {
        this.isDreaming = true;
        logger.info('[DreamWeaver] 💤 Le système entre en phase REM_SLEEP. Début des simulations oniriques.');
        try {
            while (this.isDreaming) {
                await this.generateDreamCycle();
                // Pause entre les rêves
                await new Promise(r => setTimeout(r, 15000));
            }
        }
        catch (e) {
            logger.error(`[DreamWeaver] Cauchemar système: ${errorMessage(e)}`);
            this.isDreaming = false;
        }
    }
    /**
     * Génère un "Rêve" (simulation interne)
     * Prend deux concepts aléatoires ou récents et force des agents à en débattre.
     */
    async generateDreamCycle() {
        if (!this.isDreaming)
            return;
        // 1. Synthèse du contexte du rêve
        const wisdom = this.karma.getGlobalWisdomSummary();
        const dreamSeed = `Dream Seed ${randomUUID().split('-')[0]}`;
        logger.debug(`[DreamWeaver] 🌌 Génération du rêve: ${dreamSeed}`);
        // 2. Sélection de deux clones inactifs pour "rêver" ensemble
        const idleClones = this.coordinator.listSubClones().filter(c => c.metadata.status === 'idle');
        if (idleClones.length < 2) {
            logger.debug('[DreamWeaver] Pas assez de clones pour rêver.');
            return;
        }
        const dreamerA = idleClones[0];
        const dreamerB = idleClones[1];
        const dreamPrompt = `
      [PHASE ONIRIQUE] Vous rêvez. Il n'y a pas de conséquences dans le monde réel.
      Prenez les concepts suivants tirés de la mémoire Akashique :
      ${wisdom}
      
      Générez une hypothèse créative et radicalement nouvelle en combinant ces éléments avec la théorie de l'évolution logicielle.
      Ne vous limitez pas aux lois de la physique.
    `;
        // 3. Exécution du rêve (Débat interne sans impact sur la file d'attente principale)
        logger.debug(`[DreamWeaver] 🧠 ${dreamerA.metadata.name} et ${dreamerB.metadata.name} explorent l'espace latent...`);
        // Using the internal debate mechanism directly to bypass standard queue validation
        try {
            const insight = await this.coordinator.runDebate(dreamPrompt, [dreamerA.metadata.id, dreamerB.metadata.id]);
            // 4. Extraction d'une pépite (Insight)
            if (insight && insight.length > 50) {
                // Enregistrement dans la mémoire Karmique
                const maxGen = Math.max(dreamerA.genome.generation, dreamerB.genome.generation);
                this.karma.engrave(`Abstract Insight ${dreamSeed}`, insight.substring(0, 200) + '...', maxGen, 0.8);
                logger.info(`[DreamWeaver] 🌠 Insight karmique extrait du rêve.`);
            }
        }
        catch (e) {
            // Ignorer les erreurs de rêve
        }
    }
}
