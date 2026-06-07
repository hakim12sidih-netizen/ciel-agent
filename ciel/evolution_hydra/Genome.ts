/**
 * ═══════════════════════════════════════════════════════════════
 * GENOME — Shim de compatibilité V1
 * ═══════════════════════════════════════════════════════════════
 *
 * DEPRECATED : utilisez `UnifiedGenome` de `./UnifiedGenome.js` directement.
 * Ce fichier existe pour la rétrocompatibilité du code qui faisait
 * `import { Genome } from './Genome.js'`.
 *
 * Comportement préservé :
 * - 4 chromosomes × 100 gènes (400 au total)
 * - Params V1 (temperature, toolWeights, etc.)
 * - Mode `legacyV1: true` : les features V2 (karma, ombre, résonance)
 *   sont initialisées à des valeurs par défaut mais les méthodes sont disponibles.
 */

import { UnifiedGenome, Gene, ChromosomeType } from './UnifiedGenome.js';
import type { UnifiedGenomeParams } from './UnifiedGenome.js';

// Ré-exports pour le code qui les importe depuis Genome.js
export { Gene, ChromosomeType };

/**
 * Genome V1 — 4 chromosomes × 100 gènes, params simples.
 * Constructeur rétro-compatible : (agentName?, params?)
 */
export class Genome extends UnifiedGenome {
  constructor(agentName: string | number = 'genome', params?: Partial<UnifiedGenomeParams>) {
    super({
      agentName: String(agentName),
      params,
      legacyV1: true,
      titanSize: false,
    });
  }
}

// Ré-exports pour d'autres types
export type { UnifiedGenomeParams };
