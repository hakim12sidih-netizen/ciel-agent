/**
 * CIRCUIT BREAKER - Pattern de résilience
 * Prévient les appels répétés à des services défaillants
 */

import logger from '../../utils/logger.js';

export type CircuitState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

export interface CircuitBreakerConfig {
  failureThreshold: number;      // Nombre d'erreurs avant d'ouvrir
  successThreshold: number;      // Nombre de succès pour fermer depuis HALF_OPEN
  timeout: number;               // Temps avant de passer à HALF_OPEN (ms)
  name: string;
}

export interface CircuitBreakerStatus {
  name: string;
  state: CircuitState;
  failureCount: number;
  successCount: number;
  lastError?: Error;
  nextRetryTime?: number;
}

/**
 * Circuit Breaker pour la tolérance aux pannes
 */
export class CircuitBreaker {
  private state: CircuitState = 'CLOSED';
  private failureCount = 0;
  private successCount = 0;
  private lastFailureTime?: number;
  private nextRetryTime?: number;
  private lastError?: Error;

  constructor(private config: CircuitBreakerConfig) {}

  /**
   * Exécute une fonction avec protection du circuit breaker
   */
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    this.checkState();

    if (this.state === 'OPEN') {
      const err = new Error(
        `[${this.config.name}] Circuit breaker is OPEN. ` +
        `Next retry at ${new Date(this.nextRetryTime!)}`
      );
      logger.error('[CIRCUIT-BREAKER] Circuit open', {
        name: this.config.name,
        nextRetry: this.nextRetryTime
      });
      throw err;
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure(error as Error);
      throw error;
    }
  }

  /**
   * Appel synchrone (si possible)
   */
  executeSync<T>(fn: () => T): T {
    this.checkState();

    if (this.state === 'OPEN') {
      throw new Error(
        `[${this.config.name}] Circuit breaker is OPEN`
      );
    }

    try {
      const result = fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure(error as Error);
      throw error;
    }
  }

  /**
   * Vérifie si le circuit breaker doit changer d'état
   */
  private checkState() {
    if (this.state === 'HALF_OPEN' && this.nextRetryTime && Date.now() > this.nextRetryTime) {
      // Rester en HALF_OPEN pour tester
    } else if (
      this.state === 'OPEN' &&
      this.nextRetryTime &&
      Date.now() > this.nextRetryTime
    ) {
      this.transitionTo('HALF_OPEN');
    }
  }

  /**
   * Gère un succès
   */
  private onSuccess() {
    if (this.state === 'HALF_OPEN') {
      this.successCount++;
      if (this.successCount >= this.config.successThreshold) {
        this.transitionTo('CLOSED');
      }
    } else if (this.state === 'CLOSED') {
      this.failureCount = 0;
    }
  }

  /**
   * Gère une erreur
   */
  private onFailure(error: Error) {
    this.lastError = error;
    this.lastFailureTime = Date.now();
    this.failureCount++;

    if (this.state === 'HALF_OPEN') {
      this.transitionTo('OPEN');
    } else if (this.failureCount >= this.config.failureThreshold) {
      this.transitionTo('OPEN');
    }
  }

  /**
   * Transition d'état
   */
  private transitionTo(newState: CircuitState) {
    const oldState = this.state;
    this.state = newState;

    logger.info('[CIRCUIT-BREAKER] State transition', {
      name: this.config.name,
      from: oldState,
      to: newState
    });

    if (newState === 'OPEN') {
      this.nextRetryTime = Date.now() + this.config.timeout;
      this.failureCount = 0;
    } else if (newState === 'HALF_OPEN') {
      this.successCount = 0;
      this.failureCount = 0;
    } else if (newState === 'CLOSED') {
      this.failureCount = 0;
      this.successCount = 0;
      this.lastError = undefined;
      this.nextRetryTime = undefined;
    }
  }

  /**
   * Retourne le statut actuel
   */
  getStatus(): CircuitBreakerStatus {
    return {
      name: this.config.name,
      state: this.state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      lastError: this.lastError,
      nextRetryTime: this.nextRetryTime
    };
  }

  /**
   * Réinitialise le circuit breaker
   */
  reset() {
    this.transitionTo('CLOSED');
  }
}

/**
 * Gestionnaire de circuit breakers
 */
export class CircuitBreakerManager {
  private breakers = new Map<string, CircuitBreaker>();

  create(config: CircuitBreakerConfig): CircuitBreaker {
    if (this.breakers.has(config.name)) {
      return this.breakers.get(config.name)!;
    }

    const breaker = new CircuitBreaker(config);
    this.breakers.set(config.name, breaker);
    return breaker;
  }

  get(name: string): CircuitBreaker | undefined {
    return this.breakers.get(name);
  }

  getStatus(name: string): CircuitBreakerStatus | undefined {
    return this.breakers.get(name)?.getStatus();
  }

  getAllStatus(): CircuitBreakerStatus[] {
    return Array.from(this.breakers.values()).map(b => b.getStatus());
  }

  reset(name: string) {
    this.breakers.get(name)?.reset();
  }

  resetAll() {
    for (const breaker of this.breakers.values()) {
      breaker.reset();
    }
  }
}

/**
 * Instance globale singleton
 */
export const globalCircuitBreakerManager = new CircuitBreakerManager();
