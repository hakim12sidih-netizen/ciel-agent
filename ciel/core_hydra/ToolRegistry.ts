import { Tool } from '../tools/Tool.js';
import logger from '../utils/logger.js';

/**
 * TOOL REGISTRY — The global index of HYDRA' capabilities.
 * It manages the discovery and invocation of tools.
 */
export class ToolRegistry {
  private tools: Map<string, Tool<any>> = new Map();

  register(tool: Tool<any>) {
    this.tools.set(tool.name, tool);
    logger.debug(`[Registry] Tool registered: ${tool.name}`);
  }

  get(name: string): Tool<any> | undefined {
    return this.tools.get(name);
  }

  getAll(): Tool<any>[] {
    return Array.from(this.tools.values());
  }

  count(): number {
    return this.tools.size;
  }
}