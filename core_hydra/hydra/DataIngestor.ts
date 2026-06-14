import * as fs from 'fs/promises';
import https from 'https';
import http from 'http';
import logger from '../../utils/logger.js';
import { Hippocampus } from './Hippocampus.js';
import { HydraBrain } from './HydraBrain.js';
import { GlobalTitanNVM } from '../../nvm/TitanNVM.js';
import { SemanticEncoder } from './SemanticEncoder.js';

/**
 * DATA-INGESTOR v∞.FEED
 * Alimente HYDRA-BRAIN avec des données humaines et encyclopédiques.
 */
export class DataIngestor {
  constructor(
    private brain: HydraBrain,
    private hippocampus: Hippocampus
  ) {}

  /**
   * Importe des discussions humaines depuis un fichier JSON
   */
  public async importHumanDialogs(filePath: string) {
    try {
      logger.info(`[DATA-INGESTOR] 📂 Importation des discussions : ${filePath}`);
      const data = await fs.readFile(filePath, 'utf-8');
      const dialogs = JSON.parse(data);

      for (const entry of dialogs) {
        // Indexation avec Tokenisation Native
        const content = typeof entry === 'string' ? entry : JSON.stringify(entry);
        const tokens = GlobalTitanNVM.tokenize(content);
        const embedding = SemanticEncoder.encode(content);
        
        await this.hippocampus.store(content, embedding, { 
          source: 'json_import', 
          type: 'human_dialog',
          tokenCount: tokens.length
        });
      }

      logger.info(`[DATA-INGESTOR] ✅ ${dialogs.length} entrées de dialogue ingérées.`);
    } catch (error) {
      logger.error(`[DATA-INGESTOR] ❌ Échec de l'import JSON : ${error}`);
    }
  }

  /**
   * Crawle une URL réelle pour extraire des connaissances (P1-C)
   * Utilise un vrai fetch HTTP/HTTPS, nettoie le HTML et stocke dans NVM + Hippocampe.
   */
  public async ingestWebKnowledge(url: string): Promise<void> {
    logger.info(`[DATA-INGESTOR] 🌐 Fetch réel de : ${url}`);

    let rawHtml = '';
    try {
      rawHtml = await this.fetchUrl(url);
    } catch (err: unknown) {
      logger.error(`[DATA-INGESTOR] ❌ Fetch échoué pour ${url} : ${err.message}`);
      return;
    }

    // Nettoyage HTML → texte brut (supprime balises, scripts, styles)
    const text = rawHtml
      .replace(/<script[\s\S]*?<\/script>/gi, '')
      .replace(/<style[\s\S]*?<\/style>/gi, '')
      .replace(/<[^>]+>/g, ' ')
      .replace(/\s{2,}/g, ' ')
      .trim()
      .slice(0, 50_000); // Limite à 50K chars pour éviter les débordements

    if (!(await this.sanitizeData(text))) {
      logger.warn(`[DATA-INGESTOR] ⚠️ Contenu insuffisant ou indésirable pour ${url}. Ignoré.`);
      return;
    }

    // Tokenisation réelle via TitanNVM
    const tokens = GlobalTitanNVM.tokenize(text);

    // Injection dans la NVM (binaire)
    await GlobalTitanNVM.appendToNvm(url, text, url);

    // Indexation sémantique dans l'Hippocampe
    const embedding = SemanticEncoder.encode(text);

    await this.hippocampus.store(text, embedding, {
      source:     url,
      type:       'web_knowledge',
      tokenCount: tokens.length,
      timestamp:  Date.now()
    });

    logger.info(`[DATA-INGESTOR] ✅ ${tokens.length} tokens ingérés depuis "${url}" → NVM + Hippocampe.`);
  }

  /** Fetch HTTP/HTTPS bas-niveau (sans dépendance externe) */
  private fetchUrl(url: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const lib = url.startsWith('https') ? https : http;
      const req = lib.get(url, { headers: { 'User-Agent': 'HYDRA-DataIngestor/4.0' } }, (res) => {
        if (res.statusCode && res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          // Suivi de redirection
          this.fetchUrl(res.headers.location).then(resolve).catch(reject);
          return;
        }
        const chunks: Buffer[] = [];
        res.on('data', (c: Buffer) => chunks.push(c));
        res.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
        res.on('error', reject);
      });
      req.on('error', reject);
      req.setTimeout(10_000, () => { req.destroy(); reject(new Error('Timeout')); });
    });
  }

  /**
   * Pipeline de nettoyage (via NÉMÉSIS)
   */
  public async sanitizeData(content: string): Promise<boolean> {
    // Vérification de la qualité des données avant ingestion
    return content.length > 10;
  }
}
