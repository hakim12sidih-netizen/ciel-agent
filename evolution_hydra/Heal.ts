import logger from '../utils/logger.js';
import { errorMessage } from '../types/index.js';
import type { QueryEngine } from '../core/QueryEngine.js';
import type { Aegis } from './Aegis.js';
import * as fs from 'fs';
import * as path from 'path';

/**
 * HEAL is the Recursive Self-Healing system of HYDRA.
 * It detects runtime failures in dynamic tools and 
 * automatically attempts to rewrite and refactor the faulty logic.
 */
export class Heal {
  private engine: QueryEngine;
  private aegis: Aegis;
  private healHistory: Map<string, number> = new Map();

  constructor(engine: QueryEngine, aegis: Aegis) {
    this.engine = engine;
    this.aegis = aegis;
    logger.info('[Heal] 🩹 Recursive Self-Repair system activated.');
  }

  /**
   * Called when a tool or system component crashes. 
   * Triggers a "Diagnostics & Mutation" cycle.
   */
  async diagnoseAndRepair(targetFile: string, error: string): Promise<boolean> {
    const filePath = path.resolve(process.cwd(), targetFile);
    if (!fs.existsSync(filePath)) return false;

    logger.error(`[Heal] 🛑 Trauma detected: ${targetFile} (Error: ${error.substring(0, 50)}...)`);
    const originalCode = fs.readFileSync(filePath, 'utf-8');

    try {
      // 1. Diagnostics: The Council analyzes the "injury"
      const repairPrompt = `System Failure detected in ${targetFile}. 
                            Error Context: ${error}
                            Original Code:\n\n${originalCode}\n\n
                            Task: REPAIR the code to fix this specific bug. 
                            Return ONLY the corrected code block. 
                            Use AEGIS-compliant safe code.`;

      let repairedCode = '';
      for await (const chunk of this.engine.query(repairPrompt)) {
        if (chunk.type === 'text') repairedCode += chunk.content;
      }

      // 2. Proof: Verify with AEGIS before applying the "Surgery"
      const proof = await this.aegis.verifyCode(targetFile, repairedCode);
      if (!proof.isSafe) {
        logger.error(`[Heal] 🛡️ AEGIS BLOCKED SURGERY: The proposed fix is unsafe.`);
        return false;
      }

      // 3. Application: Patch the file
      const backupPath = `${filePath}.bak`;
      fs.writeFileSync(backupPath, originalCode);
      logger.info(`[Heal] 💾 Backup created at ${path.basename(backupPath)}`);

      fs.writeFileSync(filePath, repairedCode);
      logger.info(`[Heal] ✨ SURGERY SUCCESSFUL. ${targetFile} has been healed and mutated.`);

      const count = this.healHistory.get(targetFile) || 0;
      this.healHistory.set(targetFile, count + 1);

      return true;

    } catch (err) {
      logger.error(`[Heal] 🚫 Fatal complication during repair: ${errorMessage(err)}`);
      return false;
    }
  }

  getStats() {
    return Array.from(this.healHistory.entries());
  }
}
