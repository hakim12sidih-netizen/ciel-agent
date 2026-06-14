import logger from '../../../utils/logger.js';
import { ToolDefinition } from '../HydraToolRegistry.js';
import { PANTHEON } from '../Pantheon.js';

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

export class CognitiveRegistry {
  public getTools(): ToolDefinition[] {
    return [
      tool(
        'delegate_to_pantheon',
        'Assign a mission to a specialized Olympian agent.',
        {
          agent_id: { type: 'string', enum: Object.keys(PANTHEON) },
          mission: { type: 'string' }
        },
        ['agent_id', 'mission']
      ),
      tool(
        'run_typhon_cortex',
        'Activate the Typhon crisis cortex for high-speed arbitration.',
        { crisis_data: { type: 'string' } },
        ['crisis_data']
      ),
      tool(
        'query_skill_graph',
        'Query Hydra SkillGraph and registry domains to discover available capabilities.',
        { node_query: { type: 'string' } },
        ['node_query']
      ),
      tool(
        'spawn_clone',
        'Spawn a specialist clone through CloneCoordinator.',
        {
          mission: { type: 'string' },
          cloneClass: { type: 'string' }
        },
        ['mission']
      ),
      tool(
        'dev_agent',
        'Launch a focused autonomous development agent for coding tasks.',
        {
          task: { type: 'string' },
          max_iterations: { type: 'number' }
        },
        ['task']
      ),
      tool(
        'council_migration',
        'Project or migrate a council member into a controlled avatar context.',
        {
          member: { type: 'string' },
          target: { type: 'string' }
        },
        ['member', 'target']
      ),
      tool(
        'omega_council_manager',
        'Feed or mutate the PyTorch super-council training loop.',
        {
          action: { type: 'string', enum: ['feed', 'mutate'] },
          topic: { type: 'string' }
        },
        ['action']
      ),
      tool(
        'hegemony_strategist',
        'Generate strategic plans and capability positioning for Hydra.',
        { objective: { type: 'string' } },
        ['objective']
      ),
      tool(
        'janus_simulation',
        'Run thesis/antithesis cognitive A/B analysis and synthesize a verdict.',
        { concept: { type: 'string' } },
        ['concept']
      ),
      tool(
        'hypnos',
        'Generate speculative high-temperature concepts without executing code.',
        {
          prompt: { type: 'string' },
          temperature: { type: 'number' }
        },
        ['prompt']
      ),
      tool(
        'zeus_chronicle',
        'Write or read persistent Zeus decrees and execution chronicles.',
        {
          action: { type: 'string', enum: ['write_decree', 'read_chronicles'] },
          content: { type: 'string' }
        },
        ['action']
      )
    ];
  }

  public async execute(name: string, args: Record<string, unknown>): Promise<string> {
    logger.info(`[COGNITIVE-REGISTRY] Executing cognitive tool: ${name}`);

    if (name === 'query_skill_graph') {
      return [
        '[SKILL GRAPH] Hydra registry domains:',
        '- cognitive: Pantheon, Typhon, SkillGraph, clones, DevAgent, Janus, Hypnos',
        '- execution: files, shell, Docker, OS, media, utility and local labs',
        '- network: web/search/crawl, authorized cyber intel, Telegram and n8n bridges',
        '- evolution: CRISPR, dialectics, imperial cycle, skills, NeuralForge',
        '- labs: UranusLab and Promethee forge',
        `Query: ${args.node_query}`
      ].join('\n');
    }

    return `[COGNITIVE] Tool '${name}' accepted by the cognitive registry. Args: ${JSON.stringify(args)}`;
  }
}
