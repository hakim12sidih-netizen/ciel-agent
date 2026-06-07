/**
 * GRACEFUL SHUTDOWN - Arrêt propre du système
 * Ferme les connexions, persiste l'état, libère les ressources
 */

import logger from '../../utils/logger.js';
import { errorMessage } from '../../types/index.js';

export interface ShutdownTask {
  name: string;
  fn: () => Promise<void>;
  timeout?: number;
}

/**
 * Gère l'arrêt propre du système
 */
export class GracefulShutdown {
  private tasks: ShutdownTask[] = [];
  private isShuttingDown = false;
  private readonly defaultTimeout = 5000; // 5 secondes par tâche

  constructor() {
    this.setupSignalHandlers();
  }

  /**
   * Enregistre une tâche d'arrêt
   */
  onShutdown(name: string, fn: () => Promise<void>, timeout?: number) {
    this.tasks.push({
      name,
      fn,
      timeout: timeout || this.defaultTimeout
    });
  }

  /**
   * Déclenche l'arrêt gracieux
   */
  async shutdown(exitCode: number = 0) {
    if (this.isShuttingDown) {
      logger.warn('[SHUTDOWN] Already shutting down, ignoring duplicate request');
      return;
    }

    this.isShuttingDown = true;
    logger.info('[SHUTDOWN] Starting graceful shutdown...');

    const errors: Array<{ task: string; error: Error }> = [];

    // Exécuter les tâches d'arrêt en séquence
    for (const task of this.tasks) {
      try {
        logger.info(`[SHUTDOWN] Executing: ${task.name}`);

        await Promise.race([
          task.fn(),
          new Promise((_, reject) =>
            setTimeout(
              () => reject(new Error(`Timeout: ${task.name}`)),
              task.timeout || this.defaultTimeout
            )
          )
        ]);

        logger.info(`[SHUTDOWN] ✓ ${task.name}`);
      } catch (error) {
        logger.error(`[SHUTDOWN] ✗ ${task.name}: ${errorMessage(error)}`);
        errors.push({
          task: task.name,
          error: error as Error
        });
      }
    }

    // Log des erreurs d'arrêt
    if (errors.length > 0) {
      logger.error('[SHUTDOWN] Some tasks failed:', {
        count: errors.length,
        tasks: errors.map(e => e.task)
      });
    }

    logger.info('[SHUTDOWN] Goodbye! 👋');
    process.exit(exitCode);
  }

  /**
   * Configure les handlers pour les signaux d'arrêt
   */
  private setupSignalHandlers() {
    const signals = ['SIGTERM', 'SIGINT', 'SIGHUP'];

    for (const signal of signals) {
      process.on(signal, () => {
        logger.info(`[SHUTDOWN] Received ${signal} signal`);
        this.shutdown(0);
      });
    }

    // Gestion des erreurs non capturées
    process.on('uncaughtException', (error) => {
      logger.error(`[SHUTDOWN] Uncaught exception: ${errorMessage(error)}`);
      this.shutdown(1);
    });

    process.on('unhandledRejection', (reason) => {
      logger.error(`[SHUTDOWN] Unhandled rejection: ${errorMessage(reason)}`);
      this.shutdown(1);
    });
  }

  /**
   * Retourne le statut
   */
  isShutting(): boolean {
    return this.isShuttingDown;
  }

  /**
   * Nombre de tâches enregistrées
   */
  taskCount(): number {
    return this.tasks.length;
  }
}

/**
 * Instance globale singleton
 */
export const globalShutdown = new GracefulShutdown();
