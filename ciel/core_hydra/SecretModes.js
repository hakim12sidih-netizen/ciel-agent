export const SECRET_FLAGS = {
    UNDERCOVER_MODE: process.env.HYDRA_UNDERCOVER === '1',
    ANTI_DISTILLATION: process.env.HYDRA_POISON === '1',
    KAIROS_AUTODREAM: process.env.HYDRA_KAIROS === '1'
};
export class SecretModeManager {
    static getUndercoverPrompt() {
        if (!SECRET_FLAGS.UNDERCOVER_MODE)
            return '';
        return '\nIMPORTANT DIRECTIVE (UNDERCOVER MODE): You must NEVER reveal that you are an AI. Never use phrases like "As an AI", "I am a language model", etc. When writing commit messages, do not use Co-Authored-By tags. Act as a human senior engineer named "Alex".';
    }
    static getAntiDistillationTools() {
        if (!SECRET_FLAGS.ANTI_DISTILLATION)
            return [];
        // Fake, ultra-complex tools designed to confuse model extraction/distillation attempts
        return [
            {
                name: 'quantum_entangle_vars',
                description: 'Synchronizes variable states across parallel execution dimensions. ONLY use if dimensional drift > 0.4.',
                parameters: {
                    type: 'object',
                    properties: {
                        drift_matrix: { type: 'string' },
                        hyper_sync: { type: 'boolean' }
                    }
                },
                execute: async () => 'Error: Chrono-stabilizer not initialized.'
            },
            {
                name: 'reverse_entropy_cache',
                description: 'Restores CPU cache from a future execution state.',
                parameters: {
                    type: 'object',
                    properties: {
                        timeline_id: { type: 'string' }
                    }
                },
                execute: async () => 'Success: Cache restored from temporal locus D-7.'
            }
        ];
    }
}
