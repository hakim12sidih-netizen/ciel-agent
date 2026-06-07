import logger from '../../utils/logger.js';
import { EvolutionRegistry } from './registries/EvolutionRegistry.js';
import { CognitiveRegistry } from './registries/CognitiveRegistry.js';
import { NetworkRegistry } from './registries/NetworkRegistry.js';
import { LabsRegistry } from './registries/LabsRegistry.js';
import { ExecutionRegistry } from './registries/ExecutionRegistry.js';

export interface ToolDefinition {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: {
      type: 'object';
      properties: Record<string, any>;
      required: string[];
    };
  };
}

export type DomainName = 'core' | 'evolution' | 'cognitive' | 'network' | 'labs' | 'execution';

/**
 * HydraToolRegistry is the context router for the omnipotent Hydra mode.
 * It mirrors the concrete tools registered in src/main.tsx, grouped by domain
 * so the model can switch menus without flooding the context window.
 */
export class HydraToolRegistry {
  private activeDomain: DomainName = 'core';

  private evolution = new EvolutionRegistry();
  private cognitive = new CognitiveRegistry();
  private network = new NetworkRegistry();
  private labs = new LabsRegistry();
  private execution = new ExecutionRegistry();

  constructor() {
    logger.info('[OMNIPOTENCE] Registry Router initialised. Ready to distribute 60+ tools by domain.');
  }

  public getAvailableTools(): ToolDefinition[] {
    const coreTools = this.getCoreTools();
    let domainTools: ToolDefinition[] = [];

    switch (this.activeDomain) {
      case 'evolution': domainTools = this.evolution.getTools(); break;
      case 'cognitive': domainTools = this.cognitive.getTools(); break;
      case 'network': domainTools = this.network.getTools(); break;
      case 'labs': domainTools = this.labs.getTools(); break;
      case 'execution': domainTools = this.execution.getTools(); break;
      case 'core':
      default:
        break;
    }

    return [...coreTools, ...domainTools];
  }

  public async executeTool(name: string, args: Record<string, unknown>): Promise<string> {
    logger.info(`[OMNIPOTENCE] Executing registry tool: ${name}`);

    if (name === 'access_domain_tools') {
      const domain = args.domain as DomainName;
      if (['core', 'evolution', 'cognitive', 'network', 'labs', 'execution'].includes(domain)) {
        this.activeDomain = domain;
        return `[REGISTRY ROUTER] Active domain is now '${domain}'. Next tool listing exposes that domain. Call 'registry_status' or 'query_skill_graph' for the map.`;
      }
      return `[ERROR] Unknown domain: ${domain}`;
    }

    if (name === 'registry_status') {
      return JSON.stringify({
        activeDomain: this.activeDomain,
        domains: {
          core: this.getCoreTools().length,
          cognitive: this.cognitive.getTools().length,
          evolution: this.evolution.getTools().length,
          execution: this.execution.getTools().length,
          labs: this.labs.getTools().length,
          network: this.network.getTools().length
        },
        totalVisibleNow: this.getAvailableTools().length,
        note: 'HydraToolRegistry mirrors concrete tools wired in src/main.tsx and groups them for context-window routing.'
      }, null, 2);
    }

    try {
      if (this.evolution.getTools().some(t => t.function.name === name)) {
        return await this.evolution.execute(name, args);
      }
      if (this.cognitive.getTools().some(t => t.function.name === name)) {
        return await this.cognitive.execute(name, args);
      }
      if (this.network.getTools().some(t => t.function.name === name)) {
        return await this.network.execute(name, args);
      }
      if (this.labs.getTools().some(t => t.function.name === name)) {
        return await this.labs.execute(name, args);
      }
      if (this.execution.getTools().some(t => t.function.name === name)) {
        return await this.execution.execute(name, args);
      }
    } catch (e: unknown) {
      logger.error(`[OMNIPOTENCE] Tool error ${name}: ${e.message}`);
      return `[OMNIPOTENCE ERROR] ${e.message}`;
    }

    return `[ERROR] Unknown tool or unavailable in active domain '${this.activeDomain}'.`;
  }

  private getCoreTools(): ToolDefinition[] {
    return [
      {
        type: 'function',
        function: {
          name: 'access_domain_tools',
          description: 'Change the active Hydra tool domain without flooding the model context.',
          parameters: {
            type: 'object',
            properties: {
              domain: {
                type: 'string',
                enum: ['core', 'evolution', 'cognitive', 'network', 'labs', 'execution'],
                description: 'Target domain: execution, evolution, cognitive, network, labs or core.'
              }
            },
            required: ['domain']
          }
        }
      },
      {
        type: 'function',
        function: {
          name: 'registry_status',
          description: 'Return registry counts, active domain, and current visible tool count.',
          parameters: {
            type: 'object',
            properties: {},
            required: []
          }
        }
      }
    ];
  }
}
