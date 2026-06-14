import * as readline from 'readline/promises';
import { stdin as input, stdout as output } from 'process';
import * as fs from 'fs';
import * as path from 'path';
import logger from '../../utils/logger.js';
export class SetupWizard {
    configPath = path.join(process.cwd(), 'hydra_config.json');
    async checkOrRunSetup() {
        if (fs.existsSync(this.configPath)) {
            try {
                const config = JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
                logger.info(`[SETUP] Configuration chargée : ${config.providerName} (${config.modelId})`);
                return config;
            }
            catch (e) {
                logger.warn(`[SETUP] Erreur de lecture de la config, relancement du wizard...`);
            }
        }
        logger.info('\n=============================================');
        logger.info('      🔥 INSTALLATION HYDRA - CERVEAU 🔥      ');
        logger.info('=============================================\n');
        const rl = readline.createInterface({ input, output });
        let config = {
            providerType: 'local',
            providerName: 'ollama',
            modelId: 'llama3'
        };
        try {
            logger.info('Quel type de modèle souhaitez-vous utiliser pour Hydra ?');
            logger.info('1. Local (Ollama, LMStudio, vLLM) - Privé et gratuit');
            logger.info('2. API Distante (OpenAI, Anthropic, Gemini) - Plus puissant');
            const typeChoice = await rl.question('> Choix (1 ou 2) [1]: ');
            config.providerType = typeChoice.trim() === '2' ? 'api' : 'local';
            if (config.providerType === 'local') {
                const providerChoice = await rl.question('\nProvider local (ollama, lmstudio) [ollama]: ');
                config.providerName = providerChoice.trim() || 'ollama';
                const modelChoice = await rl.question('Modèle à utiliser (ex: mistral, qwen2.5-coder, llama3) [mistral]: ');
                config.modelId = modelChoice.trim() || 'mistral';
                const urlChoice = await rl.question(`URL de l'API [http://localhost:11434]: `);
                config.baseUrl = urlChoice.trim() || 'http://localhost:11434';
            }
            else {
                const providerChoice = await rl.question('\nProvider API (openai, anthropic, gemini) [openai]: ');
                config.providerName = providerChoice.trim() || 'openai';
                const modelChoice = await rl.question('Modèle (ex: gpt-4o, claude-3-5-sonnet-20240620) [gpt-4o]: ');
                config.modelId = modelChoice.trim() || 'gpt-4o';
                const apiKey = await rl.question('Clé API (sera sauvegardée dans hydra_config.json): ');
                config.apiKey = apiKey.trim();
            }
            fs.writeFileSync(this.configPath, JSON.stringify(config, null, 2), 'utf8');
            logger.info(`\n[SETUP] ✅ Configuration sauvegardée dans ${this.configPath}`);
        }
        finally {
            rl.close();
        }
        return config;
    }
}
