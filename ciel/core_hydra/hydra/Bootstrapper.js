import { HydraCore } from './HydraCore.js';
import { DashboardServer } from '../../server/DashboardServer.js';
import { TelegramBridge } from '../../services/TelegramBridge.js';
import logger from '../../utils/logger.js';
import * as path from 'path';
import { SetupWizard } from './SetupWizard.js';
/**
 * HYDRA BOOTSTRAPPER v∞
 * Script de lancement pour l'ingestion et l'auto-évolution.
 */
async function boot() {
    logger.info("🔥 [BOOT] Initialisation du système TITAN-LEGION...");
    const wizard = new SetupWizard();
    const config = await wizard.checkOrRunSetup();
    logger.info(`[BOOT] Configuration active : ${config.providerName} / ${config.modelId}`);
    const hydra = new HydraCore();
    // 0. Lancement des services de communication
    new DashboardServer(hydra, 3001);
    new TelegramBridge(hydra);
    // 1. Ingestion du corpus Alpaca
    const corpusPath = path.resolve('data/web_corpus/web_alpaca.jsonl');
    logger.info(`📥 [BOOT] Ingestion du corpus : ${corpusPath}`);
    await hydra.ingestDialogs(corpusPath);
    // 2. Ingestion Wikipedia (Optionnel - Exemple)
    logger.info("🌐 [BOOT] Ingestion de la base de connaissances IA...");
    await hydra.ingestWeb("https://fr.wikipedia.org/wiki/Intelligence_artificielle");
    // 3. Activation des modules HYDRA
    logger.info("📡 [BOOT] Synchronisation des modules HYDRA (Infiltration, Forge, Social)...");
    // 4. Lancement de la Phase Onirique (Dream Phase)
    logger.info("🌙 [BOOT] Entrée en PHASE ONIRIQUE (Self-Play) pour 30 minutes.");
    await hydra.startDreaming(30);
    logger.info("✨ [BOOT] Cycle d'évolution terminé. HYDRA est maintenant plus conscient.");
}
boot().catch(err => {
    logger.error(`❌ [BOOT] Erreur critique : ${err.message}`);
    process.exit(1);
});
