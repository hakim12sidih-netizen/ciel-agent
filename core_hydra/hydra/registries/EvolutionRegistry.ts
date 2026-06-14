import logger from '../../../utils/logger.js';
import { ToolDefinition } from '../HydraToolRegistry.js';

function tool(
  name: string,
  description: string,
  properties: Record<string, any> = {},
  required: string[] = []
): ToolDefinition {
  return {
    type: 'function',
    function: {
      name,
      description,
      parameters: { type: 'object', properties, required }
    }
  };
}

export class EvolutionRegistry {
  public getTools(): ToolDefinition[] {
    return [
      tool(
        'start_dialectical_engine',
        'Launch an internal dialectical debate to force synthesis from opposing positions.',
        { topic: { type: 'string' } },
        ['topic']
      ),
      tool(
        'run_crispr_titan',
        'Apply CRISPR_Titan-style behavioral genome edits to Hydra agents.',
        {
          target_agent: { type: 'string' },
          mutation: { type: 'string' }
        },
        ['target_agent', 'mutation']
      ),
      tool(
        'trigger_imperial_cycle',
        'Run the Darwinian imperial cycle: reinforce high-fitness agents and retire weak patterns.'
      ),
      tool(
        'skill_memory',
        'Manage procedural skills: list, read, learn, or forget saved workflows.',
        {
          action: { type: 'string', enum: ['list', 'read', 'learn', 'forget'] },
          skillName: { type: 'string' },
          topic: { type: 'string' }
        },
        ['action']
      ),
      tool(
        'forge_tool',
        'Create or dynamically register a new Hydra tool under oversight.',
        {
          toolName: { type: 'string' },
          description: { type: 'string' },
          code: { type: 'string' }
        },
        ['toolName', 'description']
      ),
      tool(
        'neural_forge',
        'Control Neural Forge data and learning pipeline: status, scrape, mine, learn.',
        {
          action: { type: 'string', enum: ['status', 'scrape', 'mine', 'learn'] },
          topic: { type: 'string' }
        },
        ['action']
      ),
      tool(
        'omega_council_manager',
        'Feed training data into the council or run neural mutation/backpropagation.',
        {
          action: { type: 'string', enum: ['feed', 'mutate'] },
          topic: { type: 'string' }
        },
        ['action']
      )
    ];
  }

  public async execute(name: string, args: Record<string, unknown>): Promise<string> {
    logger.info(`[EVOLUTION-REGISTRY] Executing evolution tool: ${name}`);
    return `[EVOLUTION] Tool '${name}' accepted by the evolution registry. Args: ${JSON.stringify(args)}`;
  }
}
