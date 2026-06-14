import logger from '../utils/logger.js';
/**
 * TOOL REGISTRY — The global index of HYDRA' capabilities.
 * It manages the discovery and invocation of tools.
 */
export class ToolRegistry {
    tools = new Map();
    register(tool) {
        this.tools.set(tool.name, tool);
        logger.debug(`[Registry] Tool registered: ${tool.name}`);
    }
    get(name) {
        return this.tools.get(name);
    }
    getAll() {
        return Array.from(this.tools.values());
    }
    count() {
        return this.tools.size;
    }
}
