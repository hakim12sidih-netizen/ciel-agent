import logger from '../utils/logger.js';
import { errorMessage } from '../types/index.js';
import { randomUUID } from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
/**
 * KARMIC MEMORY
 * Mémoire persistante qui survit à la mort des clones.
 * Stocke les leçons universelles et les concepts synthétisés.
 */
export class KarmicMemory {
    engrams = new Map();
    storagePath;
    constructor(storageDir = './.titan/karma') {
        this.storagePath = storageDir;
        this.initStorage();
        this.loadKarma();
        logger.info(`[Karmic Memory] 🌌 Mémoire Akashique connectée. Engrammes: ${this.engrams.size}`);
    }
    initStorage() {
        if (!fs.existsSync(this.storagePath)) {
            fs.mkdirSync(this.storagePath, { recursive: true });
        }
    }
    loadKarma() {
        const file = path.join(this.storagePath, 'akashic_records.json');
        if (fs.existsSync(file)) {
            try {
                const data = JSON.parse(fs.readFileSync(file, 'utf8'));
                data.forEach((e) => this.engrams.set(e.id, e));
            }
            catch (e) {
                logger.error(`[Karmic Memory] Erreur lors de la lecture des mémoires karmiques: ${errorMessage(e)}`);
            }
        }
    }
    saveKarma() {
        const file = path.join(this.storagePath, 'akashic_records.json');
        fs.writeFileSync(file, JSON.stringify(Array.from(this.engrams.values()), null, 2));
    }
    /**
     * Enregistre une leçon vitale déduite par un clone ou l'orchestrateur
     */
    engrave(concept, lessonLearned, generation, emotionalResonance = 0.5) {
        const engram = {
            id: `krm_${randomUUID().split('-')[0]}`,
            concept,
            lessonLearned,
            emotionalResonance,
            generationDiscovered: generation,
            timestamp: Date.now()
        };
        this.engrams.set(engram.id, engram);
        this.saveKarma();
        logger.debug(`[Karmic Memory] 🔮 Nouvel engramme gravé: ${concept}`);
        return engram.id;
    }
    recordBirth(cloneId, genome) {
        return this.engrave(`Clone Birth ${cloneId}`, JSON.stringify(genome).slice(0, 500), 0, 0.6);
    }
    /**
     * Récupère les mémoires liées à un concept (Simulation RAG basique)
     */
    recall(query, limit = 3) {
        const queryWords = query.toLowerCase().split(' ');
        // Very basic TF-IDF / Keyword matching simulation for now
        // In production, this uses the local sentence-transformers GGUF
        const scored = Array.from(this.engrams.values()).map(engram => {
            let score = 0;
            const text = `${engram.concept} ${engram.lessonLearned}`.toLowerCase();
            queryWords.forEach(word => {
                if (text.includes(word))
                    score += 1;
            });
            // Boost by emotional resonance (importance)
            score += engram.emotionalResonance;
            return { engram, score };
        });
        return scored
            .filter(item => item.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, limit)
            .map(item => item.engram);
    }
    getGlobalWisdomSummary() {
        if (this.engrams.size === 0)
            return "Aucune sagesse karmique accumulée.";
        const sorted = Array.from(this.engrams.values())
            .sort((a, b) => b.emotionalResonance - a.emotionalResonance)
            .slice(0, 5);
        return sorted.map(e => `- [Gen ${e.generationDiscovered}] ${e.concept}: ${e.lessonLearned}`).join('\n');
    }
}
