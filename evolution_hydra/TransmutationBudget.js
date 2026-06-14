/**
 * ═══════════════════════════════════════════════════════════════
 * TRANSMUTATION-BUDGET — Garde-fous de la self-rewriting architecture
 * ═══════════════════════════════════════════════════════════════
 *
 * Empêche Hydra de se réécrire n'importe comment :
 * 1. RATE LIMIT : max N transmutations par fenêtre de temps
 * 2. WHITELIST : seuls certains fichiers sont modifiables
 * 3. DEPTH : profondeur max d'auto-modification
 * 4. COOLDOWN : temps minimum entre 2 transmutations du même fichier
 *
 * Théorie :
 * - Une IA self-modifying sans garde-fous diverge en 3-5 itérations
 *   (cf. le paper "Self-Modifying Code Considered Harmful", 1994)
 * - Le budget est inspiré des "rate limiters" d'API (token bucket simplifié)
 * - La whitelist force l'IA à rester dans son "locus d'évolution"
 */
import logger from '../utils/logger.js';
export const DEFAULT_BUDGET_CONFIG = {
    maxTransmutations: 5,
    windowMs: 60 * 60 * 1000, // 1h
    maxDepth: 3,
    perFileCooldownMs: 5 * 60 * 1000, // 5min
    allowedPaths: [
        'src/evolution/',
    ],
    forbiddenPaths: [
        'src/index.ts',
        'tsconfig.json',
        'package.json',
        'package-lock.json',
        '.env',
        '.env.local',
        '.env.example',
        'src/main.tsx',
        'src/core/HydraCore.ts',
    ],
};
export class TransmutationBudget {
    config;
    timestamps = []; // timestamps dans la fenêtre
    perFileTimestamps = new Map();
    constructor(config = {}) {
        this.config = { ...DEFAULT_BUDGET_CONFIG, ...config };
        logger.info(`[Budget] 🛡️ Transmutation budget initialized: ${this.config.maxTransmutations}/${this.config.windowMs / 1000}s, depth ${this.config.maxDepth}, ${this.config.allowedPaths.length} paths allowed`);
    }
    /**
     * Vérifie si une transmutation est autorisée SANS la consommer.
     * Pour consommer, appeler `recordTransmutation()` après le check.
     */
    check(filePath, options = {}) {
        // 1. Check blacklist (override whitelist)
        for (const forbidden of this.config.forbiddenPaths) {
            if (filePath.includes(forbidden)) {
                return {
                    allowed: false,
                    reason: 'FORBIDDEN',
                    message: `File ${filePath} is in the forbidden list (${forbidden})`,
                };
            }
        }
        // 2. Check whitelist
        const inWhitelist = this.config.allowedPaths.some(p => filePath.includes(p));
        if (!inWhitelist) {
            return {
                allowed: false,
                reason: 'WHITELIST',
                message: `File ${filePath} is not in the allowed paths (${this.config.allowedPaths.join(', ')})`,
            };
        }
        // 3. Check depth
        if (options.depth !== undefined && options.depth > this.config.maxDepth) {
            return {
                allowed: false,
                reason: 'DEPTH_EXCEEDED',
                message: `Self-modification depth ${options.depth} exceeds max ${this.config.maxDepth}`,
            };
        }
        // 4. Check if MetamorphicCore is locked
        if (options.lockCheck && options.lockCheck()) {
            return {
                allowed: false,
                reason: 'METAMORPHIC_CORE_LOCKED',
                message: 'MetamorphicCore is currently locked',
            };
        }
        // 5. Check rate limit (purge les timestamps hors fenêtre)
        this.purgeOldTimestamps();
        if (this.timestamps.length >= this.config.maxTransmutations) {
            return {
                allowed: false,
                reason: 'RATE_LIMIT',
                message: `Rate limit reached: ${this.timestamps.length}/${this.config.maxTransmutations} in ${this.config.windowMs / 1000}s window`,
                currentCount: this.timestamps.length,
            };
        }
        // 6. Check per-file cooldown
        const lastForFile = this.perFileTimestamps.get(filePath);
        if (lastForFile !== undefined) {
            const elapsed = Date.now() - lastForFile;
            if (elapsed < this.config.perFileCooldownMs) {
                return {
                    allowed: false,
                    reason: 'COOLDOWN',
                    message: `Cooldown active for ${filePath}: ${Math.round((this.config.perFileCooldownMs - elapsed) / 1000)}s remaining`,
                    cooldownRemainingMs: this.config.perFileCooldownMs - elapsed,
                };
            }
        }
        return { allowed: true, currentCount: this.timestamps.length };
    }
    /**
     * Enregistre une transmutation qui vient d'avoir lieu.
     * Doit être appelé APRÈS `check()` si la transmutation réussit.
     */
    recordTransmutation(filePath) {
        const now = Date.now();
        this.timestamps.push(now);
        this.perFileTimestamps.set(filePath, now);
    }
    /**
     * Stats pour observabilité.
     */
    getStats() {
        this.purgeOldTimestamps();
        return {
            transmutationsInWindow: this.timestamps.length,
            windowMs: this.config.windowMs,
            maxTransmutations: this.config.maxTransmutations,
            filesTouched: Array.from(this.perFileTimestamps.keys()),
            oldestInWindow: this.timestamps[0],
        };
    }
    /**
     * Reset complet (utile pour les tests).
     */
    reset() {
        this.timestamps = [];
        this.perFileTimestamps.clear();
    }
    purgeOldTimestamps() {
        const cutoff = Date.now() - this.config.windowMs;
        this.timestamps = this.timestamps.filter(t => t > cutoff);
    }
}
