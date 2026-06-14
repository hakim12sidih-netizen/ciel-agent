/**
 * REQUEST VALIDATOR - Validation & Sanitization des entrées
 * Prévient les injections, les requêtes malveillantes et les abus
 */
import logger from '../../utils/logger.js';
/**
 * Valide et assainit les requêtes utilisateur
 */
export class RequestValidator {
    static DEFAULT_CONFIG = {
        maxLength: 10000,
        minLength: 1,
        forbiddenPatterns: [
            /[<>{}|$;]/gi, // Caractères de contrôle
            /(\bscript\b|\bonload\b)/gi, // XSS patterns
            /(\b(select|insert|delete|update|drop)\b)/gi, // SQL injection
            /(\.\.\/|\.\.\\)/gi, // Path traversal
        ],
        allowHtml: false
    };
    /**
     * Valide une requête utilisateur
     */
    static validate(input, config) {
        const finalConfig = { ...this.DEFAULT_CONFIG, ...config };
        // Vérification basique
        if (!input || typeof input !== 'string') {
            return {
                valid: false,
                error: 'Input must be a non-empty string'
            };
        }
        // Vérification de longueur
        if (input.length < (finalConfig.minLength || 1)) {
            return {
                valid: false,
                error: `Input too short (minimum: ${finalConfig.minLength})`
            };
        }
        if (input.length > (finalConfig.maxLength || 10000)) {
            return {
                valid: false,
                error: `Input too long (maximum: ${finalConfig.maxLength})`
            };
        }
        // Vérification des patterns interdits
        if (finalConfig.forbiddenPatterns) {
            for (const pattern of finalConfig.forbiddenPatterns) {
                if (pattern.test(input)) {
                    return {
                        valid: false,
                        error: 'Input contains forbidden patterns or characters'
                    };
                }
            }
        }
        return {
            valid: true,
            sanitized: this.sanitize(input, finalConfig)
        };
    }
    /**
     * Assainit une chaîne pour la base de données
     */
    static sanitizeForDb(input) {
        return input
            .replace(/\0/g, '') // NULL bytes
            .replace(/\\/g, '\\\\') // Backslashes
            .replace(/'/g, "\\'") // Single quotes
            .replace(/"/g, '\\"') // Double quotes
            .trim();
    }
    /**
     * Assainit une chaîne pour HTML (échappe les caractères dangereux)
     */
    static sanitizeForHtml(input) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;',
            '/': '&#x2F;'
        };
        return input.replace(/[&<>"'\/]/g, (char) => map[char]);
    }
    /**
     * Assainit une chaîne générale
     */
    static sanitize(input, config) {
        let sanitized = input.trim();
        // Supprimer caractères de contrôle
        sanitized = sanitized.replace(/[\x00-\x1F\x7F]/g, '');
        // Normaliser espaces multiples
        sanitized = sanitized.replace(/\s+/g, ' ');
        if (!config.allowHtml) {
            sanitized = this.sanitizeForHtml(sanitized);
        }
        return sanitized;
    }
    /**
     * Valide une URL
     */
    static validateUrl(url) {
        try {
            const parsed = new URL(url);
            const allowedProtocols = ['http:', 'https:', 'ftp:'];
            if (!allowedProtocols.includes(parsed.protocol)) {
                return {
                    valid: false,
                    error: 'Invalid URL protocol'
                };
            }
            return { valid: true, sanitized: parsed.toString() };
        }
        catch (e) {
            return {
                valid: false,
                error: 'Invalid URL format'
            };
        }
    }
    /**
     * Valide une adresse email
     */
    static validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return {
                valid: false,
                error: 'Invalid email format'
            };
        }
        return { valid: true, sanitized: email.toLowerCase() };
    }
    /**
     * Valide un JSON
     */
    static validateJson(jsonString) {
        try {
            JSON.parse(jsonString);
            return { valid: true };
        }
        catch (e) {
            return {
                valid: false,
                error: 'Invalid JSON format'
            };
        }
    }
    /**
     * Log les tentatives de validation échouées (sécurité)
     */
    static logFailedValidation(input, reason, context) {
        logger.warn('[VALIDATOR] Validation failed', {
            reason,
            inputLength: input.length,
            timestamp: new Date().toISOString(),
            ...context
        });
    }
}
