import logger from '../utils/logger.js';
import { errorMessage } from '../types/index.js';
import { randomUUID } from 'crypto';
import * as fs from 'fs';
import * as path from 'path';

export interface KarmicEngram {
  id: string;
  concept: string;
  lessonLearned: string;
  emotionalResonance: number; // 0-1
  generationDiscovered: number;
  embedding?: number[]; // Pour future recherche RAG locale
  timestamp: number;
}

/**
 * KARMIC MEMORY
 * Mémoire persistante qui survit à la mort des clones.
 * Stocke les leçons universelles et les concepts synthétisés.
 */
export class KarmicMemory {
  private engrams: Map<string, KarmicEngram> = new Map();
  private storagePath: string;

  constructor(storageDir: string = './.titan/karma') {
    this.storagePath = storageDir;
    this.initStorage();
    this.loadKarma();
    logger.info(`[Karmic Memory] 🌌 Mémoire Akashique connectée. Engrammes: ${this.engrams.size}`);
  }

  private initStorage() {
    if (!fs.existsSync(this.storagePath)) {
      fs.mkdirSync(this.storagePath, { recursive: true });
    }
  }

  private loadKarma() {
    const file = path.join(this.storagePath, 'akashic_records.json');
    if (fs.existsSync(file)) {
      try {
        const data = JSON.parse(fs.readFileSync(file, 'utf8'));
        data.forEach((e: KarmicEngram) => this.engrams.set(e.id, e));
      } catch (e) {
        logger.error(`[Karmic Memory] Erreur lors de la lecture des mémoires karmiques: ${errorMessage(e)}`);
      }
    }
  }

  private saveKarma() {
    const file = path.join(this.storagePath, 'akashic_records.json');
    fs.writeFileSync(file, JSON.stringify(Array.from(this.engrams.values()), null, 2));
  }

  /**
   * Enregistre une leçon vitale déduite par un clone ou l'orchestrateur
   */
  public engrave(concept: string, lessonLearned: string, generation: number, emotionalResonance: number = 0.5): string {
    const engram: KarmicEngram = {
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

  public recordBirth(cloneId: string, genome: unknown): string {
    return this.engrave(`Clone Birth ${cloneId}`, JSON.stringify(genome).slice(0, 500), 0, 0.6);
  }

  /**
   * Récupère les mémoires liées à un concept (Simulation RAG basique)
   */
  public recall(query: string, limit: number = 3): KarmicEngram[] {
    const queryWords = query.toLowerCase().split(' ');
    
    // Very basic TF-IDF / Keyword matching simulation for now
    // In production, this uses the local sentence-transformers GGUF
    const scored = Array.from(this.engrams.values()).map(engram => {
      let score = 0;
      const text = `${engram.concept} ${engram.lessonLearned}`.toLowerCase();
      queryWords.forEach(word => {
        if (text.includes(word)) score += 1;
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

  public getGlobalWisdomSummary(): string {
    if (this.engrams.size === 0) return "Aucune sagesse karmique accumulée.";
    
    const sorted = Array.from(this.engrams.values())
      .sort((a, b) => b.emotionalResonance - a.emotionalResonance)
      .slice(0, 5);
      
    return sorted.map(e => `- [Gen ${e.generationDiscovered}] ${e.concept}: ${e.lessonLearned}`).join('\n');
  }
}
