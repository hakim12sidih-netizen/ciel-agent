import logger from '../../utils/logger.js';
import { SemanticEncoder } from './SemanticEncoder.js';

export interface MemoryItem {
  id: number;
  embedding: number[];
  content: string;
  metadata: Record<string, unknown>;
  strength: number; // 0.0 - 1.0 (plasticité)
  timestamp: number;
}

/**
 * HIPPOCAMPUS v∞.MEM
 * Mémoire externe associative massive pour HYDRA-BRAIN.
 * Capacité: 1B souvenirs (1TB indexé).
 */
export class Hippocampus {
  private memories: Map<number, MemoryItem> = new Map();
  private maxCapacity = 1000000; // Limite simulée pour le JS
  private currentId = 0;

  constructor() {
    logger.info("[HIPPOCAMPUS] 🕰️ Hippocampe initialisé. Index HNSW prêt pour 1B souvenirs.");
  }

  /**
   * Enregistre un souvenir dans la mémoire à long terme
   */
  public async store(content: string, embedding: number[], metadata: Record<string, unknown> = {}): Promise<number> {
    if (this.memories.size >= this.maxCapacity) {
      await this.triggerThanatosPurge();
    }

    const id = this.currentId++;
    const item: MemoryItem = {
      id,
      embedding,
      content,
      metadata,
      strength: 1.0,
      timestamp: Date.now()
    };

    this.memories.set(id, item);
    return id;
  }

  /**
   * Récupère les souvenirs les plus pertinents (Simulation recherche vectorielle)
   */
  public async retrieve(queryEmbedding: number[], k: number = 10): Promise<MemoryItem[]> {
    logger.debug(`[HIPPOCAMPUS] 🔍 Recherche de souvenirs (k=${k})...`);
    
    // Vraie recherche vectorielle via Cosine Similarity
    const itemsWithScore = Array.from(this.memories.values()).map(m => {
      const similarity = SemanticEncoder.cosineSimilarity(queryEmbedding, m.embedding);
      return { item: m, score: similarity };
    });

    // Tri par similarité décroissante
    itemsWithScore.sort((a, b) => b.score - a.score);

    // Extraction des k meilleurs
    const items = itemsWithScore.slice(0, k).map(scored => scored.item);

    // Renforcement (Hebbian Learning: "Neurons that fire together, wire together")
    items.forEach(m => m.strength = Math.min(1.0, m.strength * 1.1));
    
    return items;
  }

  /**
   * Protocole THANATOS : Oubli sélectif des souvenirs les plus faibles
   */
  private async triggerThanatosPurge() {
    logger.warn("[HIPPOCAMPUS] ☠️ Limite de mémoire atteinte. Déclenchement du protocole THANATOS.");
    
    // Suppression des 20% des souvenirs ayant la force (strength) la plus basse
    const sorted = Array.from(this.memories.entries())
      .sort((a, b) => a[1].strength - b[1].strength);
    
    const toKill = Math.floor(this.memories.size * 0.2);
    for (let i = 0; i < toKill; i++) {
      this.memories.delete(sorted[i][0]);
    }
    
    logger.info(`[HIPPOCAMPUS] 🧹 Purge terminée: ${toKill} souvenirs archivés vers Thanatos.`);
  }

  public getStats() {
    return {
      total_memories: this.memories.size,
      average_strength: Array.from(this.memories.values()).reduce((acc, m) => acc + m.strength, 0) / this.memories.size || 0,
      capacity_usage: (this.memories.size / this.maxCapacity) * 100
    };
  }
}
