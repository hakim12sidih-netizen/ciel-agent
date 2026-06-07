import logger from '../../utils/logger.js';
/**
 * TrajectoryCompressor (Inspiré de Hermes Agent)
 * Surveille et compresse l'historique de la conversation pour éviter de dépasser la limite de contexte.
 * Remplace les actions intermédiaires brutes par un résumé généré par le LLM [CONTEXT SUMMARY].
 */
export class TrajectoryCompressor {
    config;
    provider;
    constructor(provider, config) {
        this.provider = provider;
        this.config = {
            maxTokens: 4000,
            preserveFirstN: 5, // Garde le system prompt et les premiers échanges fondateurs
            preserveLastN: 10, // Garde les 10 derniers messages pour le contexte immédiat
            ...config
        };
    }
    /**
     * Estime très grossièrement le nombre de tokens (1 mot ~= 1.3 tokens)
     */
    estimateTokens(messages) {
        return messages.reduce((acc, msg) => {
            const words = msg.content.split(/\s+/).length;
            return acc + Math.ceil(words * 1.3);
        }, 0);
    }
    /**
     * Analyse et compresse l'historique si nécessaire.
     */
    async compressIfNeeded(history) {
        const currentTokens = this.estimateTokens(history);
        if (currentTokens < this.config.maxTokens || history.length <= (this.config.preserveFirstN + this.config.preserveLastN)) {
            return history; // Pas de compression nécessaire
        }
        logger.info(`[COMPRESSOR] Contexte trop lourd (${currentTokens} tokens). Démarrage de la compression de trajectoire...`);
        const protectedStart = history.slice(0, this.config.preserveFirstN);
        const protectedEnd = history.slice(history.length - this.config.preserveLastN);
        const middleToCompress = history.slice(this.config.preserveFirstN, history.length - this.config.preserveLastN);
        // Si on a déjà un message [CONTEXT SUMMARY] dans le bloc à compresser, on l'inclut pour le consolider
        const summaryPrompt = this.buildSummaryPrompt(middleToCompress);
        try {
            const summaryResponse = await this.provider.generateContent([{ role: 'user', content: summaryPrompt }]);
            const compressedMessage = {
                role: 'system',
                content: `[CONTEXT SUMMARY: Actions historiques compressées]\n${summaryResponse.trim()}`
            };
            const newHistory = [...protectedStart, compressedMessage, ...protectedEnd];
            logger.info(`[COMPRESSOR] ✅ Compression réussie. Ancien: ${history.length} msgs, Nouveau: ${newHistory.length} msgs.`);
            return newHistory;
        }
        catch (e) {
            logger.error(`[COMPRESSOR] ❌ Échec de la compression: ${e}`);
            // En cas d'échec, on renvoie l'historique complet pour ne rien perdre
            return history;
        }
    }
    buildSummaryPrompt(messagesToCompress) {
        let prompt = `Tu es un Trajectory Compressor. Résume factuellement les actions et conclusions de cette séquence de conversation.
Ne donne aucun conseil, ne réponds pas aux questions. Décris simplement ce qui s'est passé sous forme de points clés concis.
Garde les chemins de fichiers, les erreurs clés et les décisions de conception.

SÉQUENCE À RÉSUMER:
`;
        for (const msg of messagesToCompress) {
            // Tronquer les très longs messages dans le prompt de résumé pour éviter l'OOM du résumé lui-même
            const snippet = msg.content.length > 500 ? msg.content.substring(0, 500) + '...[TRUNCATED]' : msg.content;
            prompt += `\n[${msg.role.toUpperCase()}]: ${snippet}`;
        }
        return prompt;
    }
}
