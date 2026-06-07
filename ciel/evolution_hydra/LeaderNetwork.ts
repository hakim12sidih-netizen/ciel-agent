/**
 * ═══════════════════════════════════════════════════════════════
 * LEADER-NETWORK — EventBus pour la communication inter-Olympiens
 * ═══════════════════════════════════════════════════════════════
 *
 * PHASE 4 : refactorisé pour exposer un canal de communication
 * sémiotique (tokens émergents) en plus du canal vectoriel brut.
 *
 * Canaux disponibles :
 *  - 'discovery'          : découverte partagée
 *  - 'dm_<toFactionId>'   : message direct
 *  - 'council_order'      : ordre du Conseil (Overseer)
 *  - 'vector_exchange'    : tenseur brut (legacy, ultra-efficace)
 *  - 'token'              : NOUVEAU — token émergent (EmergentLanguage)
 *
 * Théorie :
 *  - Le canal vectoriel transporte des nombres arbitraires
 *  - Le canal token transporte du sens auto-organisé
 *  - Les deux sont complémentaires : tokens pour le sens,
 *    vecteurs pour la haute fréquence
 */

import { EventEmitter } from 'events';
import logger from '../utils/logger.js';

export interface EmergentToken {
  /** Le token composé (concaténation de primitives). */
  symbol: string;
  /** Les intentions qui ont composé le token. */
  intents: Array<{
    domain: string;
    intensity: number;
    context: string;
    phi?: number;
  }>;
  /** Valence émotionnelle (-1 = menace, 0 = neutre, +1 = opportunité). */
  valence: number;
  /** Epoch ms. */
  timestamp: number;
  /** ID de l'agent émetteur. */
  originatorId: string;
  /** ID unique du token (pour déduplication). */
  id: string;
}

class NetworkManager extends EventEmitter {
  constructor() {
    super();
    // Allow up to 100 concurrent leaders/listeners
    this.setMaxListeners(100);
  }

  // A Leader broadcasts a discovery to all other leaders and the Overseer
  broadcastDiscovery(factionId: string, title: string, discovery: string): void {
    logger.debug(`[Leader Network] 📡 ${title} broadcasts: "${discovery.substring(0, 50)}..."`);
    this.emit('discovery', { factionId, title, discovery });
  }

  // A Leader wants to discuss something specifically with another
  sendDirectMessage(fromFactionId: string, toFactionId: string, message: string): void {
    this.emit(`dm_${toFactionId}`, { fromFactionId, message });
  }

  // The Overseer (Council) sends an inescapable order to all Leaders
  transmitCouncilOrder(order: string): void {
    logger.debug(`[Council Command] ⚠️ OVERSEER TRANSMITS DIRECTIVE: ${order}`);
    this.emit('council_order', order);
  }

  // --- OMNISCIENCE: Emergent Communication ---
  // A Leader or Clone sends a RAW vector signal (tensor) to another.
  // This bypasses natural language for ultra-efficient coordination.
  broadcastVector(fromId: string, toId: string, vector: number[]): void {
    this.emit('vector_exchange', { fromId, toId, vector });
    logger.debug(`[Emergent Comm] Vector Exchange: ${fromId} ➔ ${toId} (len: ${vector.length})`);
  }

  /**
   * PHASE 4 : diffuse un token émergent (sémiotique) sur le réseau.
   * Contrairement à broadcastVector, le token est du SENS — pas juste
   * un tenseur. Les listeners peuvent l'interpréter via EmergentLanguage.
   */
  broadcastToken(token: EmergentToken): void {
    logger.debug(`[Leader Network] 🗣️ Token: ${token.symbol} from ${token.originatorId} (valence: ${token.valence.toFixed(2)})`);
    this.emit('token', token);
  }

  /**
   * Variante "broadcast" ciblé : envoie un token à un agent spécifique.
   * Utilise le canal direct.
   */
  sendTokenTo(toId: string, token: EmergentToken): void {
    logger.debug(`[Leader Network] 📨 Token to ${toId}: ${token.symbol}`);
    this.emit(`token_${toId}`, token);
  }
}

export const LeaderNetwork = new NetworkManager();
