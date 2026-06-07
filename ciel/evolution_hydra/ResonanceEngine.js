import { LeaderNetwork } from './LeaderNetwork.js';
import { CloneClass } from '../core/clones/CloneTypes.js';
import logger from '../utils/logger.js';
export class ResonanceEngine {
    coordinator;
    knowledge = new Map();
    constructor(coordinator) {
        this.coordinator = coordinator;
        logger.debug('[Resonance Engine] Swarm consensus layer activated.');
        LeaderNetwork.on('discovery', async (data) => {
            if (this.knowledge.has(data.discovery)) {
                this.handleConfirmation(data.factionId, data.discovery);
            }
            else {
                await this.initiateInquisition(data.factionId, data.discovery);
            }
        });
    }
    async initiateInquisition(originalFactionId, discovery) {
        this.knowledge.set(discovery, {
            discovery,
            sourceFactionId: originalFactionId,
            confirmers: [],
            status: 'suspect',
            createdAt: Date.now()
        });
        try {
            const inquisitorId = await this.coordinator.createClone(`Inquisitor_${Math.random().toString(36).slice(2, 5)}`, `Verification mission: confirm or refute this discovery: "${discovery}".`, CloneClass.TEMPORARY);
            this.coordinator.runCloneTask(inquisitorId, `Verify this fact: "${discovery}"`).catch((err) => {
                logger.error(`[Resonance Engine] Inquisitor ${inquisitorId} failed: ${err.message}`);
            });
        }
        catch (err) {
            const message = err instanceof Error ? err.message : String(err);
            logger.error(`[Resonance Engine] Could not spawn Inquisitor: ${message}`);
        }
    }
    handleConfirmation(factionId, discovery) {
        const truth = this.knowledge.get(discovery);
        if (!truth || truth.sourceFactionId === factionId)
            return;
        if (!truth.confirmers.includes(factionId)) {
            truth.confirmers.push(factionId);
            if (truth.confirmers.length >= 2) {
                truth.status = 'truth';
                LeaderNetwork.broadcastDiscovery('system', 'Resonance Engine', `[VETTED_TRUTH] ${truth.discovery}`);
            }
        }
    }
}
