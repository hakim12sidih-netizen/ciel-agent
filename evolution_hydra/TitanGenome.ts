/**
 * ═══════════════════════════════════════════════════════════════
 * TITAN GENOME — Shim de compatibilité V3
 * ═══════════════════════════════════════════════════════════════
 *
 * DEPRECATED : utilisez `UnifiedGenome` de `./UnifiedGenome.js` directement
 * avec l'option `titanSize: true`.
 *
 * Comportement préservé :
 * - 4 chromosomes massifs : 4096 + 8192 + 2048 + 4096 = 18 432 gènes
 * - agentName et dnaHash comme dans l'original
 * - Constructeur rétro-compatible : (agentName, genesis = true)
 */

import crypto from 'crypto';
import { UnifiedGenome, Gene, ChromosomeType } from './UnifiedGenome.js';

// Ré-exports
export { Gene, ChromosomeType };

/**
 * TitanGenome — 18 432 gènes au total.
 * Constructeur rétro-compatible : (agentName, genesis = true)
 */
export class TitanGenome extends UnifiedGenome {
  constructor(agentName: string, genesis: boolean = true) {
    super({
      agentName,
      titanSize: true,
      legacyV1: false,
      noGenesis: !genesis,
    });
  }

  /**
   * Sérialise avec les gènes complets (format Titan d'origine).
   */
  public override serialize(): string {
    const data = {
      name: this.agentName,
      gen: this.generation,
      fitness: this.fitnessHistory,
      genes: {
        struct: this.g_struct.map(g => [g.value, g.h3k4me3, g.h3k27me3, g.dna_methylation]),
        behavior: this.g_behavior.map(g => [g.value, g.h3k4me3, g.h3k27me3, g.dna_methylation]),
        epi: this.g_epi.map(g => [g.value, g.h3k4me3, g.h3k27me3, g.dna_methylation]),
        meta: this.g_meta.map(g => [g.value, g.h3k4me3, g.h3k27me3, g.dna_methylation]),
      },
    };
    return JSON.stringify(data);
  }
}
