/**
 * 🧠 TITAN-NVM : High-Performance Neural Virtual Memory
 * Gère la hiérarchie de mémoire du HYDRA-BRAIN (L1 à L4)
 */
import logger from '../utils/logger.js';

export const MemoryLevel = {
    L1_HOT: "L1_HOT",       // 48GB - Registres actifs
    L2_WARM: "L2_WARM",     // 96GB - Contexte session
    L3_BRAIN: "L3_BRAIN",   // 400GB - Savoir consolidé
    L4_ARCHIVE: "L4_ARCHIVE" // 1.1TB - Archives compressées
} as const;

export type MemoryLevel = typeof MemoryLevel[keyof typeof MemoryLevel];

export interface MemoryChunk {
    id: string;
    content: unknown;
    vector?: number[];
    timestamp: number;
    accessCount: number;
}

export class TitanNVM {
    private storage: Map<MemoryLevel, Map<string, MemoryChunk>> = new Map();

    constructor() {
        Object.values(MemoryLevel).forEach((level: string) => {
            this.storage.set(level as MemoryLevel, new Map());
        });
    }

    /**
     * Stocke une information dans le niveau de mémoire spécifié
     */
    async store(level: MemoryLevel, chunk: Partial<MemoryChunk>): Promise<void> {
        const fullChunk: MemoryChunk = {
            id: chunk.id || Math.random().toString(36).substring(7),
            content: chunk.content,
            vector: chunk.vector,
            timestamp: Date.now(),
            accessCount: 0
        };
        this.storage.get(level)!.set(fullChunk.id, fullChunk);
        logger.info(`[TNVM] Stored in ${level}: ${fullChunk.id}`);
    }

    /**
     * Récupération intelligente (RAG interne)
     */
    async retrieve(id: string): Promise<MemoryChunk | null> {
        for (const level of [MemoryLevel.L1_HOT, MemoryLevel.L2_WARM, MemoryLevel.L3_BRAIN]) {
            const chunk = this.storage.get(level)!.get(id);
            if (chunk) {
                chunk.accessCount++;
                return chunk;
            }
        }
        return null;
    }
}
