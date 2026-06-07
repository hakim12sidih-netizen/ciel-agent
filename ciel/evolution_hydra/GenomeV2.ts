/**
 * ═══════════════════════════════════════════════════════════════
 * GENOME V2 — Shim de compatibilité
 * ═══════════════════════════════════════════════════════════════
 *
 * DEPRECATED : utilisez `UnifiedGenome` de `./UnifiedGenome.js` directement.
 *
 * Comportement préservé :
 * - 4 chromosomes × 100 gènes (V1 sizing, pas Titan)
 * - Toutes les features V2 actives : épigénome, karma, ombre, résonance, méta
 * - Constructeur rétro-compatible : (generation, params?)
 */

import { UnifiedGenome, Gene, ChromosomeType } from './UnifiedGenome.js';
import type {
  EpigeneticMarker,
  KarmicRecord,
  ShadowProfile,
  ResonanceSignature,
  UnifiedGenomeParams,
} from './UnifiedGenome.js';

// Ré-exports des types V2
export { Gene, ChromosomeType };
export type {
  EpigeneticMarker,
  KarmicRecord,
  ShadowProfile,
  ResonanceSignature,
  UnifiedGenomeParams,
};

/**
 * GenomeV2 — complet avec features V2.
 * Constructeur rétro-compatible : (generation, params?)
 */
export class GenomeV2 extends UnifiedGenome {
  constructor(generation: number, params?: Partial<UnifiedGenomeParams>) {
    super({
      agentName: `gnm_v2_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      generation,
      params,
      titanSize: false,
      legacyV1: false,
    });
  }
}
