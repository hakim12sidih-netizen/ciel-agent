import logger from '../../../utils/logger.js';
function tool(name, description, properties = {}, required = []) {
    return {
        type: 'function',
        function: {
            name,
            description,
            parameters: { type: 'object', properties, required }
        }
    };
}
export class LabsRegistry {
    getTools() {
        return [
            tool('run_uranus_experiment', 'Launch an isolated UranusLab investigation.', { hypothesis: { type: 'string' } }, ['hypothesis']),
            tool('ignite_promethee_forge', 'Generate a new architecture or innovation through the Promethee forge.', { target_concept: { type: 'string' } }, ['target_concept']),
            tool('python_lab', 'Run a Python experiment in an isolated lab container.', {
                code: { type: 'string' },
                requirements: { type: 'array', items: { type: 'string' } },
                timeout: { type: 'number' }
            }, ['code']),
            tool('universal_lab', 'Run a polyglot experiment in an isolated Docker lab.', {
                language: { type: 'string', enum: ['python', 'node', 'rust', 'go', 'bash', 'csharp', 'cpp'] },
                code: { type: 'string' },
                packages: { type: 'array', items: { type: 'string' } }
            }, ['language', 'code']),
            tool('pandora_sandbox', 'Run static safety analysis on unknown code without executing it.', {
                code: { type: 'string' },
                language: { type: 'string' }
            }, ['code'])
        ];
    }
    async execute(name, args) {
        logger.info(`[LABS-REGISTRY] Lab tool accepted: ${name}`);
        return `[LABS] Tool '${name}' accepted by the labs registry. Args: ${JSON.stringify(args)}`;
    }
}
