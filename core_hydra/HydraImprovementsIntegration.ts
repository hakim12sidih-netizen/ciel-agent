/**
 * HYDRA IMPROVEMENTS INTEGRATION
 * Intègre tous les systèmes d'amélioration dans HydraCore
 * 
 * A importer et utiliser dans HydraCore.ts :
 * import { initializeHydraImprovements } from './HydraImprovementsIntegration.js';
 * initializeHydraImprovements(hydra);
 */

import logger from '../utils/logger.js';
import { RequestValidator } from './middleware/RequestValidator.js';
import { RateLimiter, globalRateLimiter } from './middleware/RateLimiter.js';
import { globalMetrics } from './monitoring/MetricsCollector.js';
import { globalCircuitBreakerManager } from './resilience/CircuitBreaker.js';
import { globalCache } from './cache/DistributedCache.js';
import { globalShutdown } from './lifecycle/GracefulShutdown.js';
import { globalProfiler } from './profiling/AgentProfiler.js';
import { createLoadBalancer } from './orchestration/LoadBalancer.js';

export interface HydraImprovementsConfig {
  enableRateLimiting?: boolean;
  enableMetrics?: boolean;
  enableCaching?: boolean;
  enableCircuitBreaker?: boolean;
  enableProfiling?: boolean;
  enableLoadBalancing?: boolean;
  maxRequestSize?: number;
  cacheDefaultTtl?: number;
  rateLimitConfig?: {
    user: number;
    api_external: number;
    agent: number;
    global: number;
  };
}

/**
 * Initialise tous les systèmes d'amélioration dans Hydra
 */
export function initializeHydraImprovements(
  hydra: HydraHost,
  config?: HydraImprovementsConfig
) {
  const finalConfig: Required<HydraImprovementsConfig> = {
    enableRateLimiting: true,
    enableMetrics: true,
    enableCaching: true,
    enableCircuitBreaker: true,
    enableProfiling: true,
    enableLoadBalancing: true,
    maxRequestSize: 10000,
    cacheDefaultTtl: 300,
    rateLimitConfig: {
      user: 100,
      api_external: 50,
      agent: 1000,
      global: 5000
    },
    ...config
  };

  logger.info('[HYDRA-IMPROVEMENTS] Initializing improvements...');

  // 1. Rate Limiting
  if (finalConfig.enableRateLimiting) {
    initializeRateLimiting(hydra, finalConfig);
  }

  // 2. Request Validation
  initializeValidation(hydra, finalConfig);

  // 3. Metrics Collection
  if (finalConfig.enableMetrics) {
    initializeMetrics(hydra, finalConfig);
  }

  // 4. Circuit Breaker
  if (finalConfig.enableCircuitBreaker) {
    initializeCircuitBreaker(hydra, finalConfig);
  }

  // 5. Caching
  if (finalConfig.enableCaching) {
    initializeCaching(hydra, finalConfig);
  }

  // 6. Agent Profiling
  if (finalConfig.enableProfiling) {
    initializeProfiling(hydra, finalConfig);
  }

  // 7. Load Balancing
  if (finalConfig.enableLoadBalancing) {
    initializeLoadBalancing(hydra, finalConfig);
  }

  // 8. Graceful Shutdown
  initializeShutdown(hydra, finalConfig);

  logger.info('[HYDRA-IMPROVEMENTS] ✅ All improvements initialized');
}

/**
 * Minimal interface for the Hydra host injected into improvement modules.
 * Avoids `any` while still allowing test mocks.
 */
interface HydraHost {
  think: (input: string, ...args: unknown[]) => Promise<unknown>;
  persistState?: () => Promise<void>;
  [key: string]: unknown;
}

/**
 * Initialise le rate limiting
 */
function initializeRateLimiting(hydra: HydraHost, config: Required<HydraImprovementsConfig>) {
  const rateLimiter = new RateLimiter(config.rateLimitConfig);

  // Wrapper original pour passer par rate limiter
  const originalThink = hydra.think.bind(hydra);
  hydra.think = async (input: string, userId?: string) => {
    const userIdentifier = userId || 'anonymous';
    const allowed = await rateLimiter.acquire(userIdentifier, 'user');

    if (!allowed) {
      const status = rateLimiter.getStatus(userIdentifier, 'user');
      const error = new Error(
        `Rate limit exceeded. Reset at ${new Date(status.resetTime)}`
      );
      logger.warn('[RATE-LIMIT] Request blocked', { userId: userIdentifier });
      throw error;
    }

    return originalThink(input);
  };

  hydra.getRateLimiterStatus = (userId?: string) =>
    rateLimiter.getStatus(userId || 'anonymous', 'user');

  logger.info('[RATE-LIMITER] Initialized');
}

/**
 * Initialise la validation des requêtes
 */
function initializeValidation(hydra: HydraHost, config: Required<HydraImprovementsConfig>) {
  // Wrapper original
  const originalThink = hydra.think.bind(hydra);
  hydra.think = async (input: string, ...args: unknown[]) => {
    // Valider l'input
    const validation = RequestValidator.validate(input, {
      maxLength: config.maxRequestSize
    });

    if (!validation.valid) {
      RequestValidator.logFailedValidation(input, validation.error || 'Unknown');
      throw new Error(`Invalid request: ${validation.error}`);
    }

    return originalThink(validation.sanitized || input, ...args);
  };

  hydra.validateInput = (input: string) => RequestValidator.validate(input);

  logger.info('[VALIDATOR] Initialized');
}

/**
 * Initialise les métriques
 */
function initializeMetrics(hydra: HydraHost, config: Required<HydraImprovementsConfig>) {
  const originalThink = hydra.think.bind(hydra);
  hydra.think = async (input: string, ...args: unknown[]) => {
    const startTime = performance.now();

    try {
      const result = await originalThink(input, ...args);
      const latency = performance.now() - startTime;

      const primaryAgent = result.agentsUsed?.[0] || 'unknown';
      globalMetrics.recordRequest(latency, primaryAgent, result.success, input.length);

      return result;
    } catch (error) {
      const latency = performance.now() - startTime;
      globalMetrics.recordRequest(latency, 'error', false);
      throw error;
    }
  };

  hydra.getMetrics = () => globalMetrics.getMetrics();
  hydra.getAgentMetrics = (agentId: string) => globalMetrics.getAgentMetrics(agentId);

  logger.info('[METRICS] Initialized');
}

/**
 * Initialise les circuit breakers
 */
function initializeCircuitBreaker(hydra: HydraHost, config: Required<HydraImprovementsConfig>) {
  const cbManager = globalCircuitBreakerManager;

  // Créer des circuit breakers pour les services critiques
  cbManager.create({
    name: 'titan_nvm',
    failureThreshold: 5,
    successThreshold: 2,
    timeout: 30000
  });

  cbManager.create({
    name: 'agent_execution',
    failureThreshold: 3,
    successThreshold: 2,
    timeout: 10000
  });

  hydra.getCircuitBreakerStatus = (name: string) =>
    cbManager.getStatus(name);
  hydra.getAllCircuitBreakers = () =>
    cbManager.getAllStatus();

  logger.info('[CIRCUIT-BREAKER] Initialized with 2 breakers');
}

/**
 * Initialise le caching
 */
function initializeCaching(hydra: HydraHost, config: Required<HydraImprovementsConfig>) {
  const cache = globalCache;

  // Wrapper pour cacher les résultats de raisonnement similaires
  const originalThink = hydra.think.bind(hydra);
  hydra.think = async (input: string, ...args: unknown[]) => {
    const cacheKey = `hydra:think:${input.slice(0, 100)}`;

    // Essayer le cache
    const cached = cache.get(cacheKey);
    if (cached) {
      logger.debug('[CACHE] Cache hit', { key: cacheKey });
      return cached;
    }

    // Exécuter et cacher
    const result = await originalThink(input, ...args);
    cache.set(cacheKey, result, config.cacheDefaultTtl);

    return result;
  };

  hydra.getCacheStats = () => cache.getStats();
  hydra.invalidateCache = (pattern?: RegExp) => {
    if (pattern) {
      return cache.deletePattern(pattern);
    }
    cache.clear();
    return 0;
  };

  logger.info('[CACHE] Initialized');
}

/**
 * Initialise le profiling d'agents
 */
function initializeProfiling(hydra: HydraHost, config: Required<HydraImprovementsConfig>) {
  const profiler = globalProfiler;
  const originalThink = hydra.think.bind(hydra);

  hydra.think = async (input: string, ...args: unknown[]) => {
    const startTime = performance.now();

    try {
      const result = await originalThink(input, ...args);
      const latency = performance.now() - startTime;

      // Profiler chaque agent utilisé
      for (const agentId of result.agentsUsed || []) {
        profiler.recordExecution(agentId, latency, result.success);
      }

      return result;
    } catch (error) {
      const latency = performance.now() - startTime;
      throw error;
    }
  };

  hydra.getAgentProfile = (agentId: string) => profiler.getProfile(agentId);
  hydra.getProfileStats = () => profiler.getStats();
  hydra.getUnderperformers = (threshold?: number) =>
    profiler.getUnderperformers(threshold);

  logger.info('[PROFILER] Initialized');
}

/**
 * Initialise le load balancer
 */
function initializeLoadBalancing(hydra: HydraHost, config: Required<HydraImprovementsConfig>) {
  const loadBalancer = createLoadBalancer(globalProfiler, 'adaptive');

  hydra.selectAgentForLoad = (candidates: string[], priority?: 'speed' | 'accuracy' | 'balanced') =>
    loadBalancer.selectAgent(candidates, priority);

  hydra.getLoadInfo = (agents: string[]) => loadBalancer.getLoadInfo(agents);
  hydra.getHealthiestAgent = (agents: string[]) => loadBalancer.getHealthiest(agents);

  logger.info('[LOAD-BALANCER] Initialized');
}

/**
 * Initialise le graceful shutdown
 */
function initializeShutdown(hydra: HydraHost, config: Required<HydraImprovementsConfig>) {
  const shutdown = globalShutdown;

  // Enregistrer les tâches d'arrêt
  shutdown.onShutdown('persist_metrics', async () => {
    const metrics = globalMetrics.getMetrics();
    logger.info('[SHUTDOWN] Final metrics', {
      requests: metrics.requestCount,
      avgLatency: metrics.avgLatency.toFixed(2) + 'ms'
    });
  });

  shutdown.onShutdown('flush_cache', async () => {
    const stats = globalCache.getStats();
    logger.info('[SHUTDOWN] Cache flushed', {
      entries: stats.entries,
      hitRate: stats.hitRate.toFixed(1) + '%'
    });
    globalCache.clear();
  });

  shutdown.onShutdown('persist_state', async () => {
    if (hydra.persistState) {
      await hydra.persistState();
      logger.info('[SHUTDOWN] State persisted');
    }
  });

  logger.info('[GRACEFUL-SHUTDOWN] Initialized');
}

/**
 * Exports des instances globales pour utilisation directe
 */
export {
  globalRateLimiter,
  globalMetrics,
  globalCircuitBreakerManager,
  globalCache,
  globalShutdown,
  globalProfiler
};
