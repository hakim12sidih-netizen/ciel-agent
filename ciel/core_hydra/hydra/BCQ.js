import { EventEmitter } from 'events';
import logger from '../../utils/logger.js';
/**
 * BCQ — Bus Quantique de Cohérence
 * Protocole de consensus inter-agents temps réel.
 * Les agents soumettent des propositions; ZEUS arbitre la décision finale.
 */
export class BCQ extends EventEmitter {
    pendingProposals = new Map();
    consensusHistory = [];
    agentScores = new Map();
    constructor() {
        super();
    }
    /** Un agent soumet une proposition sur un ticket de délibération */
    submitProposal(ticketId, proposal) {
        const existing = this.pendingProposals.get(ticketId) ?? [];
        existing.push(proposal);
        this.pendingProposals.set(ticketId, existing);
        logger.debug(`[BCQ] 📨 Proposal from ${proposal.agentId.toUpperCase()} (ticket: ${ticketId})`);
    }
    /**
     * ZEUS arbitre les propositions pour un ticket donné.
     * Stratégie : choisir la proposition avec le score de confiance le plus élevé,
     * puis laisser ZEUS synthétiser une décision finale.
     */
    async arbitrate(ticketId, zeusDecider) {
        const proposals = this.pendingProposals.get(ticketId) ?? [];
        // Quorum minimum
        if (proposals.length < 3) {
            throw new Error(`[BCQ] Quorum non atteint pour le ticket ${ticketId} (minimum 3, actuel ${proposals.length})`);
        }
        logger.info(`[BCQ] ⚖️ ZEUS arbitrating ${proposals.length} proposals for ticket ${ticketId}`);
        // Calcul du score pondéré avec historique
        const scoredProposals = proposals.map(p => {
            const stats = this.agentScores.get(p.agentId) || { wins: 0, total: 0 };
            const winRate = stats.total > 0 ? stats.wins / stats.total : 0.5; // neutre par défaut
            const finalScore = (p.confidence * 0.7) + (winRate * 0.3);
            return { ...p, finalScore };
        });
        scoredProposals.sort((a, b) => b.finalScore - a.finalScore);
        // Détection de divergence
        if (scoredProposals.length >= 2) {
            const diff = scoredProposals[0].finalScore - scoredProposals[1].finalScore;
            if (diff < 0.05) {
                logger.warn(`[BCQ] ⚠️ Forte divergence détectée (écart ${(diff * 100).toFixed(1)}%). Appel à un arbitrage complexe requis.`);
            }
        }
        const winner = scoredProposals[0];
        const finalDecision = await zeusDecider(proposals);
        const dissent = proposals.filter((p) => p.agentId !== winner.agentId);
        // Mise à jour de l'historique
        proposals.forEach(p => {
            const stats = this.agentScores.get(p.agentId) || { wins: 0, total: 0 };
            stats.total++;
            if (p.agentId === winner.agentId)
                stats.wins++;
            this.agentScores.set(p.agentId, stats);
        });
        const result = {
            finalDecision,
            winningAgent: winner.agentId,
            agreement: Math.max(0, Math.min(1, winner.finalScore)),
            dissent,
            timestamp: Date.now(),
        };
        this.consensusHistory.push(result);
        this.pendingProposals.delete(ticketId);
        this.emit('consensus', result);
        logger.info(`[BCQ] ✅ Consensus reached. Winner: ${winner.agentId.toUpperCase()}`);
        return result;
    }
    async runConsensus(ticketId, proposals) {
        for (const proposal of proposals) {
            this.submitProposal(ticketId, proposal);
        }
        return this.arbitrate(ticketId, async (items) => {
            const winner = [...items].sort((a, b) => b.confidence - a.confidence)[0];
            return winner.content;
        });
    }
    getHistory() {
        return [...this.consensusHistory];
    }
    clearTicket(ticketId) {
        this.pendingProposals.delete(ticketId);
    }
}
