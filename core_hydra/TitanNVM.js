/**
 * 🧠 TITAN-NVM : High-Performance Neural Virtual Memory
 * Gère la hiérarchie de mémoire du HYDRA-BRAIN (L1 à L4)
 */
export const MemoryLevel = {
    L1_HOT: "L1_HOT", // 48GB - Registres actifs
    L2_WARM: "L2_WARM", // 96GB - Contexte session
    L3_BRAIN: "L3_BRAIN", // 400GB - Savoir consolidé
    L4_ARCHIVE: "L4_ARCHIVE" // 1.1TB - Archives compressées
};
export class TitanNVM {
    storage = new Map();
    constructor() {
        Object.values(MemoryLevel).forEach((level) => {
            this.storage.set(level, new Map());
        });
    }
    /**
     * Stocke une information dans le niveau de mémoire spécifié
     */
    async store(level, chunk) {
        const fullChunk = {
            id: chunk.id || Math.random().toString(36).substring(7),
            content: chunk.content,
            vector: chunk.vector,
            timestamp: Date.now(),
            accessCount: 0
        };
        this.storage.get(level).set(fullChunk.id, fullChunk);
        logger.info(`[TNVM] Stored in ${level}: ${fullChunk.id}`);
    }
    /**
     * Récupération intelligente (RAG interne)
     */
    async retrieve(id) {
        for (const level of [MemoryLevel.L1_HOT, MemoryLevel.L2_WARM, MemoryLevel.L3_BRAIN]) {
            const chunk = this.storage.get(level).get(id);
            if (chunk) {
                chunk.accessCount++;
                return chunk;
            }
        }
        return null;
    }
}
