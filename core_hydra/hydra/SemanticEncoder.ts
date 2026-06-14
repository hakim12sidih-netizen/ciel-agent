import { GlobalTitanNVM } from '../../nvm/TitanNVM.js';

/**
 * SEMANTIC ENCODER
 * Encode du texte en vecteurs de dimension 64 pour l'Hippocampus.
 * Combine la fréquence de n-grams, un TF-IDF simplifié et un hachage du contenu.
 */
export class SemanticEncoder {
  public static readonly DIMENSIONS = 64;

  /**
   * Encode un texte en un vecteur de 64 dimensions, normalisé.
   */
  public static encode(text: string): number[] {
    const vector = new Array(this.DIMENSIONS).fill(0);
    const tokens = GlobalTitanNVM.tokenize(text);
    
    if (tokens.length === 0) {
      return vector; // Vecteur nul si texte vide
    }

    // 1. Distribution de fréquences basique (pseudo TF)
    for (let i = 0; i < tokens.length; i++) {
      const token = tokens[i];
      // Hasher le token pour obtenir un index (0-63)
      const index = Math.abs(this.hashString(token)) % this.DIMENSIONS;
      vector[index] += 1;
      
      // Bi-grams (contexte local)
      if (i < tokens.length - 1) {
        const bigram = token + tokens[i + 1];
        const bgIndex = Math.abs(this.hashString(bigram)) % this.DIMENSIONS;
        vector[bgIndex] += 0.5;
      }
    }

    // 2. Normalisation L2 (Cosine Similarity ready)
    let magnitude = 0;
    for (let i = 0; i < this.DIMENSIONS; i++) {
      magnitude += vector[i] * vector[i];
    }
    
    magnitude = Math.sqrt(magnitude);
    
    if (magnitude > 0) {
      for (let i = 0; i < this.DIMENSIONS; i++) {
        vector[i] = vector[i] / magnitude;
      }
    }

    return vector;
  }

  /**
   * Calcule la similarité cosinus entre deux vecteurs (0 = opposé, 1 = identique)
   */
  public static cosineSimilarity(vecA: number[], vecB: number[]): number {
    if (vecA.length !== vecB.length) return 0;
    
    let dotProduct = 0;
    let normA = 0;
    let normB = 0;
    
    for (let i = 0; i < vecA.length; i++) {
      dotProduct += vecA[i] * vecB[i];
      normA += vecA[i] * vecA[i];
      normB += vecB[i] * vecB[i];
    }
    
    if (normA === 0 || normB === 0) return 0;
    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
  }

  private static hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return hash;
  }
}
