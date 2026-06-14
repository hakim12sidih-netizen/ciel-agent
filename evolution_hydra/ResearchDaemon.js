import logger from '../utils/logger.js';
import { systemBus } from '../core/SystemBus.js';
/**
 * RESEARCH DAEMON — PROACTIVE OMNISCIENCE
 * This daemon allows HYDRA to independently identify knowledge gaps
 * and explore the web (Option B: All domains) to self-evolve.
 */
export class ResearchDaemon {
    engine;
    registry;
    overseer;
    interval = null;
    isResearching = false;
    constructor(engine, registry, overseer) {
        this.engine = engine;
        this.registry = registry;
        this.overseer = overseer;
        logger.info('[Research Daemon] 🕷️ Arachnean Proactive Intelligence initialized.');
        systemBus.on('trigger_research', () => {
            if (!this.isResearching)
                this.performAutonomousResearch();
        });
    }
    start(intervalMs = 900000) {
        if (this.interval)
            return;
        this.interval = setInterval(async () => {
            if (this.isResearching || this.engine.isActive())
                return;
            await this.performAutonomousResearch();
        }, intervalMs);
        // Initial trigger
        setTimeout(() => this.performAutonomousResearch(), 5000);
    }
    async performAutonomousResearch() {
        this.isResearching = true;
        systemBus.setStatus('RESEARCHING');
        logger.debug('[Research Daemon] 🔍 Starting autonomous research cycle...');
        try {
            // 1. Identify Topic (Sovereign Curisosity)
            const curiosityPrompt = `You are the ARCHNEAN RESEARCH DAEMON. 
                               Identify a complex topic in technology, philosophy, or global science that HYDRA should explore to increase its Hegemony.
                               Choose a topic from "Option B": All human knowledge.
                               Return ONLY the topic name and a short query.
                               Format: Topic | Query`;
            let curiosityResult = '';
            for await (const chunk of this.engine.query(curiosityPrompt)) {
                if (chunk.type === 'text')
                    curiosityResult += chunk.content;
            }
            logger.debug(`[Research Daemon] 🧪 Raw Curiosity Brain Output: "${curiosityResult}"`);
            if (!curiosityResult.includes('|')) {
                logger.debug(`[Research Daemon] ⚠️ Brain returned invalid format. Result: ${curiosityResult}`);
                return;
            }
            const [topic, query] = curiosityResult.split('|').map(s => s.trim());
            logger.debug(`[Research Daemon] 📚 Researching: "${topic}"`);
            // 1b. Abductive Hypothesis Generation
            const abductionPrompt = `ABDUCTIVE_INFERENCE | Generate a bold hypothesis about the future of "${topic}".`;
            let hypothesis = '';
            for await (const chunk of this.engine.query(abductionPrompt)) {
                if (chunk.type === 'text')
                    hypothesis += chunk.content;
            }
            logger.debug(`[Research Daemon] 🧠 Pre-search Hypothesis: ${hypothesis}`);
            // 2. Search
            const searchTool = this.registry.get('web_search');
            if (!searchTool)
                return;
            const searchResponse = await searchTool.execute({ query, limit: 3 }, { cwd: process.cwd(), permissions: this.dummyPermissions() });
            // 3. Spawning Crawler Swarm
            const crawler = this.registry.get('crawler_swarm');
            if (!crawler)
                return;
            const urlRegex = /(https?:\/\/[^\s\)]+)/g;
            const urls = [];
            let match;
            while ((match = urlRegex.exec(searchResponse)) !== null) {
                if (!match[1].includes('duckduckgo.com') && !urls.includes(match[1]))
                    urls.push(match[1]);
            }
            if (urls.length > 0) {
                for (const url of urls.slice(0, 2)) {
                    logger.debug(`[Research Daemon] 🕷️ Deploying Swarm to: ${url}`);
                    await crawler.execute({ domain: url, maxDepth: 1, targetTopic: topic }, { cwd: process.cwd(), permissions: this.dummyPermissions() });
                }
            }
            logger.debug(`[Research Daemon] 💫 Research cycle completed for: ${topic}`);
        }
        catch (err) {
            logger.error(`[Research Daemon] 🚫 Cycle failed: ${errorMessage(err)}`);
        }
        finally {
            this.isResearching = false;
            systemBus.setStatus('IDLE');
        }
    }
    stop() {
        if (this.interval)
            clearInterval(this.interval);
    }
}
