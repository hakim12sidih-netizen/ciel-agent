/**
 * ═══════════════════════════════════════════════════════════════
 * I-LLM-CLIENT — Abstraction minimale pour LLM
 * ═══════════════════════════════════════════════════════════════
 *
 * Pas besoin de recréer un provider complet : LLMTransmuter veut
 * juste `complete(prompt) → text`. On abstrait cette seule méthode
 * pour pouvoir mocker le LLM dans les tests.
 *
 * Si un LLMProvider complet (GroqProvider, OllamaProvider, etc.)
 * est disponible, on l'enveloppe via `wrapProvider()`.
 */
/**
 * Wrapper optionnel pour transformer un LLMProvider en ILLMClient.
 * L'import est dynamique pour éviter de casser le graphe de modules.
 */
export async function wrapProvider(provider) {
    return {
        name: provider.name,
        isAvailable: () => provider.isAvailable(),
        async complete(prompt, options = {}) {
            const messages = options.systemPrompt
                ? [
                    { role: 'system', content: options.systemPrompt },
                    { role: 'user', content: prompt },
                ]
                : [{ role: 'user', content: prompt }];
            let full = '';
            for await (const chunk of provider.chat(messages, {
                maxTokens: options.maxTokens ?? 4096,
                temperature: options.temperature ?? 0.3,
            })) {
                if (chunk.type === 'text' && chunk.content) {
                    full += chunk.content;
                }
                else if (chunk.type === 'error') {
                    throw new Error(`LLM error: ${chunk.error ?? 'unknown'}`);
                }
            }
            return full;
        },
    };
}
/**
 * MockLLMClient pour les tests et le mode offline.
 * Répond des textes pré-enregistrés en fonction du prompt.
 */
export class MockLLMClient {
    name = 'mock';
    responses = [];
    callLog = [];
    failQueue = [];
    /** Répond `text` à tout prompt contenant `match`. */
    onPrompt(match, text) {
        this.responses.push({ match, response: text });
        return this;
    }
    /** Prochaine invocation throw une erreur avec ce message. */
    failOnce(message = 'mock LLM error') {
        this.failQueue.push(message);
        return this;
    }
    async complete(prompt, options) {
        this.callLog.push({ prompt, options });
        if (this.failQueue.length > 0) {
            const msg = this.failQueue.shift();
            throw new Error(msg);
        }
        for (const r of this.responses) {
            if (typeof r.match === 'string') {
                if (prompt.includes(r.match))
                    return r.response;
            }
            else {
                if (r.match.test(prompt))
                    return r.response;
            }
        }
        return '// no mock response configured\n';
    }
    async isAvailable() {
        return true;
    }
    /** Historique des appels (debug / tests). */
    getCalls() {
        return [...this.callLog];
    }
}
