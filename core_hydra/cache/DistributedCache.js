/**
 * DISTRIBUTED CACHE - Caching multi-niveau avec TTL
 * Optimise les accès répétés aux données
 */
import logger from '../../utils/logger.js';
/**
 * Cache distribué avec support TTL et statistiques
 */
export class DistributedCache {
    cache = new Map();
    stats = {
        hits: 0,
        misses: 0,
        evictions: 0
    };
    maxEntries = 10000;
    defaultTtl = 300; // 5 minutes
    cleanupInterval = 60000; // 1 minute
    constructor() {
        this.startAutoCleanup();
    }
    /**
     * Définit une valeur dans le cache
     */
    set(key, value, ttlSeconds = this.defaultTtl) {
        // Vérifier la limite de taille (LRU eviction)
        if (this.cache.size >= this.maxEntries &&
            !this.cache.has(key)) {
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
    get(key) {
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
        return entry.value;
    }
    /**
     * Supprime une clé
     */
    delete(key) {
        return this.cache.delete(key);
    }
    /**
     * Supprime toutes les clés avec pattern
     */
    deletePattern(pattern) {
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
    clear() {
        this.cache.clear();
        this.stats = { hits: 0, misses: 0, evictions: 0 };
    }
    /**
     * Obtient les statistiques du cache
     */
    getStats() {
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
    evictLru() {
        let lruKey = null;
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
    cleanup() {
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
     * Démarre le nettoyage automatique
     */
    startAutoCleanup() {
        setInterval(() => this.cleanup(), this.cleanupInterval);
    }
    /**
     * Existe-t-il?
     */
    has(key) {
        const entry = this.cache.get(key);
        if (!entry)
            return false;
        if (Date.now() > entry.expiry) {
            this.cache.delete(key);
            return false;
        }
        return true;
    }
    /**
     * Taille du cache
     */
    size() {
        return this.cache.size;
    }
}
/**
 * Instance globale singleton
 */
export const globalCache = new DistributedCache();
