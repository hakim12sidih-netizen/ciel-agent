import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { Tool as HERMES_Tool, ToolContext } from '../../tools/Tool.js';
import logger from '../../utils/logger.js';
import { errorMessage } from '../../types/index.js';
import * as fs from 'fs';
import * as path from 'path';

/**
 * MCP HOST — L'Intégrateur Natif
 * Gère les connexions aux serveurs MCP externes et expose leurs outils à HYDRA.
 */
export class MCPHost {
  private clients: Map<string, Client> = new Map();
  private configPath: string;

  constructor() {
    this.configPath = path.join(process.cwd(), 'config', 'mcp_servers.json');
  }

  async initialize() {
    if (!fs.existsSync(this.configPath)) {
      this.saveConfig({ servers: {} });
    }

    const config = JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
    for (const [name, serverConfig] of Object.entries<{ command: string; args?: string[]; env?: Record<string, string> }>(config.servers)) {
      try {
        await this.connectToServer(name, serverConfig);
      } catch (e) {
        logger.error(`[MCP] Failed to connect to server ${name}: ${errorMessage(e)}`);
      }
    }
  }

  private async connectToServer(name: string, config: { command: string; args?: string[]; env?: Record<string, string> }) {
    logger.info(`[MCP] Connecting to server ${name}...`);
    
    const env = Object.fromEntries(
      Object.entries({ ...process.env, ...(config.env || {}) })
        .filter((entry): entry is [string, string] => typeof entry[1] === 'string')
    );

    const transport = new StdioClientTransport({
      command: config.command,
      args: config.args || [],
      env
    });

    const client = new Client(
      { name: 'HYDRA-Host', version: '1.0.0' },
      { capabilities: {} }
    );

    await client.connect(transport);
    this.clients.set(name, client);
    logger.info(`[MCP] 🔗 Server ${name} connected successfully.`);
  }

  async getExternalTools(): Promise<HERMES_Tool[]> {
    const allTools: HERMES_Tool[] = [];

    for (const [serverName, client] of this.clients.entries()) {
      try {
        const response = await client.listTools();
        for (const tool of response.tools) {
          allTools.push(this.wrapMCPTool(serverName, tool));
        }
      } catch (e) {
        logger.error(`[MCP] Failed to list tools for ${serverName}: ${e}`);
      }
    }

    return allTools;
  }

  private wrapMCPTool(serverName: string, mcpTool: { name: string; description?: string; inputSchema: Record<string, unknown> }): HERMES_Tool {
    const host = this;
    return {
      name: `mcp_${serverName}_${mcpTool.name}`,
      description: `[MCP: ${serverName}] ${mcpTool.description ?? ''}`,
      parameters: mcpTool.inputSchema,
      execute: async (args: Record<string, unknown>, _context: ToolContext) => {
        const client = host.clients.get(serverName);
        if (!client) throw new Error(`MCP Server ${serverName} disconnected.`);
        
        const result = await client.callTool({
          name: mcpTool.name,
          arguments: args
        });

        // Convert result to string
        return JSON.stringify(result.content);
      }
    } as HERMES_Tool;
  }

  private saveConfig(config: Record<string, unknown>) {
    const dir = path.dirname(this.configPath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(this.configPath, JSON.stringify(config, null, 2));
  }
}

// Singleton for easy access
export const mcpHost = new MCPHost();
