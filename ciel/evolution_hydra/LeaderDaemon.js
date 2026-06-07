import { LeaderNetwork } from './LeaderNetwork.js';
import logger from '../utils/logger.js';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
const execAsync = promisify(exec);
/**
 * LeaderDaemon orchestrates the autonomous behavior of Faction Leaders.
 * They run in the background (all at once as requested).
 * Updated to support Imperial Orders from the Council.
 */
export class LeaderDaemon {
    ga;
    engine;
    intervalMs;
    timer = null;
    isProcessing = false;
    currentImperialOrder = null;
    constructor(ga, engine, intervalMs = 60000) {
        this.ga = ga;
        this.engine = engine;
        this.intervalMs = intervalMs;
        // Listen for high-priority Council Orders
        LeaderNetwork.on('council_order', (order) => {
            logger.debug(`[Leader Daemon] ⚠️ ALL LEADERS REDIRECTED BY COUNCIL: ${order}`);
            this.currentImperialOrder = order;
        });
    }
    start() {
        if (this.timer)
            return;
        logger.debug(`[Leader Daemon] Activated. Faction Leaders will now pursue their wills every ${this.intervalMs / 1000}s.`);
        this.timer = setInterval(async () => {
            if (this.isProcessing)
                return;
            const factions = this.ga.factions || [];
            if (factions.length === 0)
                return;
            this.isProcessing = true;
            logger.debug(`[Leader Daemon] ⚡ Awakening ${factions.length} Faction Leaders...`);
            try {
                await Promise.all(factions.map(async (faction) => {
                    const leader = this.ga.population.find(g => g.id === faction.leaderId);
                    if (!leader)
                        return;
                    try {
                        // Priority Check: Is there an Imperial Order?
                        const objective = this.currentImperialOrder || faction.will;
                        const isCouncilOrder = !!this.currentImperialOrder;
                        logger.debug(`[Leader Daemon] 👑 ${faction.title} of '${faction.name}' is acting on ${isCouncilOrder ? 'COUNCIL ORDER' : 'WILL'}: "${objective}"`);
                        // 1. "Trainer" logic: Scrape the web based on the objective
                        const searchTask = `Task for Leader ${faction.title}: ${objective}. 
                               Research technical info for model training. 
                               Summarize for PyTorch ingestion.`;
                        let researchData = '';
                        for await (const chunk of this.engine.query(searchTask)) {
                            if (chunk.type === 'text')
                                researchData += chunk.content;
                        }
                        // 2. Training logic
                        const pyScriptPath = path.join(process.cwd(), 'src', 'council', 'pytorch', 'train_council.py');
                        await execAsync(`python "${pyScriptPath}"`);
                        // 3. Network Broadcast
                        const discovery = `[${isCouncilOrder ? 'ORDER_COMPLETION' : 'WILL_DISCOVERY'}] ${researchData.substring(0, 200)}...`;
                        LeaderNetwork.broadcastDiscovery(faction.id, faction.title, discovery);
                    }
                    catch (err) {
                        logger.error(`[Leader Daemon] Leader ${faction.id} failed its cycle: ${err.message}`);
                    }
                }));
                // Clear the order after a complete cycle of obedience across all factions
                if (this.currentImperialOrder) {
                    logger.debug(`[Leader Daemon] ✅ Imperial Order processing cycle complete.`);
                    this.currentImperialOrder = null;
                }
            }
            finally {
                this.isProcessing = false;
            }
        }, this.intervalMs);
    }
    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
}
