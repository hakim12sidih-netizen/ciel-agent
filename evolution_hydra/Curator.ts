import * as fs from 'fs';
import * as path from 'path';
import logger from '../utils/logger.js';
import { LLMProvider } from '../providers/Provider.js';

export interface CuratorConfig {
  skillsDir: string;
  staleAfterDays: number;
}

/**
 * Le CURATOR (Inspiré de Hermes Agent)
 * Agent d'arrière-plan qui nettoie, organise et consolide (Umbrella-building) 
 * la bibliothèque de compétences (skills) générées pendant les sessions.
 */
export class Curator {
  private provider: LLMProvider;
  private config: CuratorConfig;
  private archiveDir: string;
  private referencesDir: string;

  constructor(provider: LLMProvider, config?: Partial<CuratorConfig>) {
    this.provider = provider;
    this.config = {
      skillsDir: path.join(process.cwd(), 'skills'),
      staleAfterDays: 30, // Archive après 30 jours sans accès
      ...config
    };
    
    this.archiveDir = path.join(this.config.skillsDir, '.archive');
    this.referencesDir = path.join(this.config.skillsDir, 'references');

    this.ensureDirectories();
  }

  private ensureDirectories() {
    [this.config.skillsDir, this.archiveDir, this.referencesDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  /**
   * Lance le cycle complet du Curator.
   * Doit être appelé quand le système est inactif (ex: DreamPhase).
   */
  public async runMaintenanceCycle() {
    logger.info("🧹 [CURATOR] Début du cycle de maintenance de la mémoire...");
    
    try {
      await this.pruneStaleSkills();
      await this.buildUmbrellas();
      logger.info("🧹 [CURATOR] ✅ Maintenance terminée.");
    } catch (e) {
      logger.error(`[CURATOR] Erreur durant la maintenance: ${e}`);
    }
  }

  /**
   * Archive les compétences qui n'ont pas été modifiées ou consultées depuis trop longtemps.
   */
  private async pruneStaleSkills() {
    const files = fs.readdirSync(this.config.skillsDir)
      .filter(f => f.endsWith('.md') && !f.startsWith('.'));

    const now = Date.now();
    let archivedCount = 0;

    for (const file of files) {
      const fullPath = path.join(this.config.skillsDir, file);
      const stats = fs.statSync(fullPath);
      const daysSinceLastModify = (now - stats.mtime.getTime()) / (1000 * 3600 * 24);

      if (daysSinceLastModify > this.config.staleAfterDays) {
        const destPath = path.join(this.archiveDir, file);
        fs.renameSync(fullPath, destPath);
        archivedCount++;
      }
    }

    if (archivedCount > 0) {
      logger.info(`[CURATOR] Pruning: ${archivedCount} compétences archivées (>${this.config.staleAfterDays}j).`);
    }
  }

  /**
   * Analyse les compétences récentes et consolide (fusionne) les compétences similaires.
   */
  private async buildUmbrellas() {
    const files = fs.readdirSync(this.config.skillsDir)
      .filter(f => f.endsWith('.md') && !f.startsWith('.'));

    if (files.length < 2) return; // Pas assez de fichiers pour fusionner

    logger.info(`[CURATOR] Analyse de ${files.length} compétences pour Umbrella-building...`);

    // Récupérer un résumé de chaque fichier pour le LLM
    const skillSummaries = files.map(file => {
      const content = fs.readFileSync(path.join(this.config.skillsDir, file), 'utf8');
      const snippet = content.substring(0, 300); // 300 premiers chars pour le clustering
      return `Fichier: ${file}\nAperçu: ${snippet}\n---`;
    }).join('\n');

    const prompt = `Tu es le Curator, responsable de l'organisation de ma mémoire.
Voici une liste de petites compétences (skills). Trouve celles qui parlent du même sujet et propose de les fusionner en une compétence "Parapluie" (Umbrella).
Réponds UNIQUEMENT en JSON avec ce format exact :
{
  "umbrellas": [
    {
      "new_umbrella_name": "python_debugging.md",
      "files_to_merge": ["debug_script.md", "fix_error_py.md"],
      "reason": "Les deux traitent du débogage Python"
    }
  ]
}
Si rien ne mérite d'être fusionné, renvoie {"umbrellas": []}.
\nCOMPÉTENCES:\n${skillSummaries}`;

    try {
      const response = await this.provider.generateContent([{ role: 'user', content: prompt }]);
      // Extraire le JSON de la réponse
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const plan = JSON.parse(jsonMatch[0]);
        if (plan.umbrellas && plan.umbrellas.length > 0) {
          await this.executeMergePlan(plan.umbrellas);
        } else {
          logger.debug("[CURATOR] Aucune fusion nécessaire.");
        }
      }
    } catch (e) {
      logger.error(`[CURATOR] Échec de l'Umbrella-building: ${e}`);
    }
  }

  /**
   * Exécute les fusions proposées par le LLM.
   */
  private async executeMergePlan(umbrellas: Array<{ new_umbrella_name: string; files_to_merge: string[] }>) {
    for (const umbrella of umbrellas) {
      if (!umbrella.new_umbrella_name || !umbrella.files_to_merge || umbrella.files_to_merge.length < 2) {
        continue;
      }

      logger.info(`[CURATOR] Création Umbrella '${umbrella.new_umbrella_name}' depuis ${umbrella.files_to_merge.length} fichiers.`);
      
      let mergedContent = `# ${umbrella.new_umbrella_name.replace('.md', '')}\n\n`;
      mergedContent += `*Consolidé automatiquement par le Curator.*\n\n`;

      for (const file of umbrella.files_to_merge) {
        const fullPath = path.join(this.config.skillsDir, file);
        if (fs.existsSync(fullPath)) {
          const content = fs.readFileSync(fullPath, 'utf8');
          mergedContent += `## Origine: ${file}\n${content}\n\n---\n\n`;
          
          // Demotion : déplacer le fichier original vers references/ au lieu de le supprimer
          const destPath = path.join(this.referencesDir, file);
          fs.renameSync(fullPath, destPath);
        }
      }

      const umbrellaPath = path.join(this.config.skillsDir, umbrella.new_umbrella_name);
      fs.writeFileSync(umbrellaPath, mergedContent, 'utf8');
    }
  }
}
