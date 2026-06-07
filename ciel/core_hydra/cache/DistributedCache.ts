/**
 * DISTRIBUTED CACHE - Caching multi-niveau avec TTL
 * Optimise les accès répétés aux données
 */

import logger from '../../utils/logger.js';
import { scheduler } from '../../polyglot/scheduler.js';

export interface CacheEntry<T> {
  value: T;
  expiry: number;
  hits: number;
  created: number;
}

export interface CacheStats {
  entries: number;
  hits: number;
  misses: number;
  hitRate: number;
  avgHits: number;
}

/**
 * Cache distribué avec support TTL et statistiques
 */
export class DistributedCache {
  private cache = new Map<string, CacheEntry<any>>();
  private stats = {
    hits: 0,
    misses: 0,
    evictions: 0
  };

  private readonly maxEntries = 10000;
  private readonly defaultTtl = 300; // 5 minutes
  private readonly cleanupInterval = 60000; // 1 minute

  constructor() {
    this.startAutoCleanup();
  }

  /**
   * Définit une valeur dans le cache
   */
  set<T>(key: string, value: T, ttlSeconds = this.defaultTtl): void {
    // Vérifier la limite de taille (LRU eviction)
    if (
      this.cache.size >= this.maxEntries &&
      !this.cache.has(key)
    ) {
      this.evictLru();
    }

    this.cache.set(key, {
      value,
      expiry: Date.now() + ttlSeconds * 1000,
      hits: 0,
      created: Date.now()
    });
  }

  /**
   * Récupère une valeur du cache
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      this.stats.misses++;
      return null;
    }

    // Vérifier expiration
    if (Date.now() > entry.expiry) {
      this.cache.delete(key);
      this.stats.misses++;
      return null;
    }

    // Incrémenter hits
    entry.hits++;
    this.stats.hits++;

    return entry.value as T;
  }

  /**
   * Supprime une clé
   */
  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  /**
   * Supprime toutes les clés avec pattern
   */
  deletePattern(pattern: RegExp): number {
    let deleted = 0;
    for (const key of this.cache.keys()) {
      if (pattern.test(key)) {
        this.cache.delete(key);
        deleted++;
      }
    }
    return deleted;
  }

  /**
   * Vide complètement le cache
   */
  clear(): void {
    this.cache.clear();
    this.stats = { hits: 0, misses: 0, evictions: 0 };
  }

  /**
   * Obtient les statistiques du cache
   */
  getStats(): CacheStats {
    const totalRequests = this.stats.hits + this.stats.misses;
    const hitRate = totalRequests > 0 ? (this.stats.hits / totalRequests) * 100 : 0;
    const avgHits = this.cache.size > 0
      ? Array.from(this.cache.values()).reduce((sum, e) => sum + e.hits, 0) /
        this.cache.size
      : 0;

    return {
      entries: this.cache.size,
      hits: this.stats.hits,
      misses: this.stats.misses,
      hitRate,
      avgHits
    };
  }

  /**
   * Éviction LRU (Least Recently Used)
   */
  private evictLru() {
    let lruKey: string | null = null;
    let lruTime = Date.now();

    for (const [key, entry] of this.cache) {
      if (entry.created < lruTime) {
        lruTime = entry.created;
        lruKey = key;
      }
    }

    if (lruKey) {
      this.cache.delete(lruKey);
      this.stats.evictions++;
      logger.debug('[CACHE] LRU eviction', { key: lruKey });
    }
  }

  /**
   * Nettoie les entrées expirées
   */
  private cleanup() {
    const now = Date.now();
    let cleaned = 0;

    for (const [key, entry] of this.cache) {
      if (now > entry.expiry) {
        this.cache.delete(key);
        cleaned++;
      }
    }

    if (cleaned > 0) {
      logger.debug('[CACHE] Cleanup', { cleaned });
    }
  }

  /**
   * Démarre le nettoyage automatique (via polyglot scheduler)
   */
  private startAutoCleanup() {
    scheduler.schedule('distributed_cache_cleanup', this.cleanupInterval, () => this.cleanup())
      .catch((e) => {
        logger.warn(`[DistributedCache] scheduler.schedule failed, using raw setInterval: ${e instanceof Error ? e.message : e}`);
        setInterval(() => this.cleanup(), this.cleanupInterval);
      });
  }

  /**
   * Existe-t-il?
   */
  has(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;
    if (Date.now() > entry.expiry) {
      this.cache.delete(key);
      return false;
    }
    return true;
  }

  /**
   * Taille du cache
   */
  size(): number {
    return this.cache.size;
  }
}

/**
 * Instance globale singleton
 */
export const globalCache = new DistributedCache();
