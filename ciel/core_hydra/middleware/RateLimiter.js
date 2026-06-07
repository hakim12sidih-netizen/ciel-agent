/**
 * RATE LIMITER - Limitation de débit & Anti-abuse
 * Empêche les abus par user, API externe ou agent
 */
import logger from '../../utils/logger.js';
/**
 * Implémente le rate limiting avec fenêtres glissantes
 */
export class RateLimiter {
    queues = new Map();
    windowMs = 60000; // 1 minute
    config = {
        user: 100,
        api_external: 50,
        agent: 1000,
        global: 5000
    };
    globalRequests = [];
    cleanup = setInterval(() => this.cleanupQueues(), 300000); // 5 min
    constructor(config) {
        if (config) {
            this.config = { ...this.config, ...config };
        }
    }
    /**
     * Vérifie et enregistre une requête (retourne true si OK, false si throttlée)
     */
    async acquire(identifier, type = 'user') {
        const now = Date.now();
        // Vérifier limite globale
        this.globalRequests = this.globalRequests.filter(t => now - t < this.windowMs);
        if (this.globalRequests.length >= this.config.global) {
            logger.warn('[RATE-LIMITER] Global limit exceeded', {
                identifier,
                type,
                global: this.globalRequests.length
            });
            return false;
        }
        // Vérifier limite spécifique
        const limit = this.config[type];
        const key = `${type}:${identifier}`;
        if (!this.queues.has(key)) {
            this.queues.set(key, []);
        }
        const times = this.queues.get(key);
        const recentRequests = times.filter(t => now - t < this.windowMs);
        if (recentRequests.length >= limit) {
            logger.warn('[RATE-LIMITER] Limit exceeded', {
                identifier,
                type,
                current: recentRequests.length,
                limit
            });
            return false;
        }
        // Enregistrer la requête
        recentRequests.push(now);
        this.queues.set(key, recentRequests);
        this.globalRequests.push(now);
        return true;
    }
    /**
     * Retourne l'état du rate limit pour un identifiant
     */
    getStatus(identifier, type = 'user') {
        const now = Date.now();
        const key = `${type}:${identifier}`;
        const limit = this.config[type];
        const times = this.queues.get(key) || [];
        const recentRequests = times.filter(t => now - t < this.windowMs);
        const remaining = Math.max(0, limit - recentRequests.length);
        // Temps du prochain reset
        const resetTime = recentRequests.length > 0
            ? recentRequests[0] + this.windowMs
            : now + this.windowMs;
        return {
            identifier,
            type,
            remaining,
            resetTime,
            isThrottled: remaining === 0
        };
    }
    /**
     * Réinitialise la limite pour un identifiant
     */
    reset(identifier, type = 'user') {
        const key = `${type}:${identifier}`;
        this.queues.delete(key);
    }
    /**
     * Réinitialise tous les rate limits
     */
    resetAll() {
        this.queues.clear();
        this.globalRequests = [];
    }
    /**
     * Nettoie les anciens enregistrements
     */
    cleanupQueues() {
        const now = Date.now();
        for (const [key, times] of this.queues) {
            const recent = times.filter(t => now - t < this.windowMs);
            if (recent.length === 0) {
                this.queues.delete(key);
            }
            else {
                this.queues.set(key, recent);
            }
        }
        this.globalRequests = this.globalRequests.filter(t => now - t < this.windowMs);
    }
    /**
     * Destruction du rate limiter
     */
    destroy() {
        clearInterval(this.cleanup);
        this.queues.clear();
        this.globalRequests = [];
    }
}
/**
 * Instance globale singleton
 */
export const globalRateLimiter = new RateLimiter();
