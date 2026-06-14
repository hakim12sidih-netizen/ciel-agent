import type { LLMProvider, Message, ChatOptions, StreamChunk, ToolCall, ToolDefinition } from '../providers/Provider.js';
import { CostTracker } from './CostTracker.js';
import { ContextCollector } from './ContextCollector.js';
import { SYSTEM_PROMPT } from '../config/defaults.js';
import { estimateTokens } from '../utils/tokenizer.js';
import logger from '../utils/logger.js';
import { SecretModeManager } from './SecretModes.js';
import { GlobalTitanNVM } from '../nvm/TitanNVM.js';

export interface ToolHandler {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  execute: (args: Record<string, unknown>) => Promise<string>;
}

export interface QueryEngineCallbacks {
  onText?: (text: string) => void;
  onToolCall?: (name: string, args: Record<string, unknown>) => void;
  onToolResult?: (name: string, result: string) => void;
  onError?: (error: string) => void;
  onDone?: (usage: { inputTokens: number; outputTokens: number }) => void;
}

export class QueryEngine {
  private provider: LLMProvider;
  private messages: Message[] = [];
  private costTracker: CostTracker;
  private contextCollector: ContextCollector;
  private tools: Map<string, ToolHandler> = new Map();
  private model: string;
  private systemPrompt: string;
  private maxToolLoops: number;
  private temperature: number;
  private maxTokens: number;
  private isProcessing = false;

  constructor(opts: {
    provider: LLMProvider;
    model: string;
    systemPrompt?: string;
    tools?: ToolHandler[];
    maxToolLoops?: number;
    temperature?: number;
    maxTokens?: number;
  }) {
    this.provider = opts.provider;
    this.model = opts.model;
    this.systemPrompt = opts.systemPrompt || SYSTEM_PROMPT;
    this.maxToolLoops = opts.maxToolLoops ?? 25;
    this.temperature = opts.temperature ?? 0.7;
    this.maxTokens = opts.maxTokens ?? 4096;
    this.costTracker = new CostTracker(this.model);
    this.contextCollector = new ContextCollector();

    if (opts.tools) {
      for (const tool of opts.tools) this.tools.set(tool.name, tool);
    }
  }

  registerTool(handler: ToolHandler) { this.tools.set(handler.name, handler); }
  unregisterTool(name: string) { this.tools.delete(name); }

  /** Met à jour le systemPrompt (utilisé pour les clones spécialisés). */
  setSystemPrompt(prompt: string): void { this.systemPrompt = prompt; }

  /** Accès read-only au systemPrompt courant. */
  getSystemPrompt(): string { return this.systemPrompt; }

  /** Retourne tous les tools enregistrés (pour les clones). */
  getAllTools(): ToolHandler[] { return Array.from(this.tools.values()); }

  getToolDefinitions(): ToolDefinition[] {
    return Array.from(this.tools.values()).map(t => ({
      type: 'function' as const,
      function: { name: t.name, description: t.description, parameters: t.parameters },
    }));
  }

  async *query(userMessage: string, callbacks?: QueryEngineCallbacks): AsyncGenerator<StreamChunk> {
    if (this.isProcessing) {
      yield { type: 'error', error: 'Already processing a query' };
      return;
    }

    this.isProcessing = true;
    try {
      this.messages.push({ role: 'user', content: userMessage });

      const contextInfo = this.contextCollector.formatForPrompt();
      const fullSystemPrompt = `${this.systemPrompt}\n\n--- Environment ---\n${contextInfo}${SecretModeManager.getUndercoverPrompt()}`;

      // TITAN-NVM : Mappage mémoire prédictif pour le modèle courant
      // Simulation d'un appel au layer_id=0, offset=0
      GlobalTitanNVM.accessLayer(0, 0, 1024 * 1024);

      let toolLoopCount = 0;

      while (toolLoopCount < this.maxToolLoops) {
        const chatOpts: ChatOptions = {
          model: this.model,
          temperature: this.temperature,
          maxTokens: this.maxTokens,
          topP: 0.9,
          systemPrompt: fullSystemPrompt,
          tools: this.tools.size > 0 ? this.getToolDefinitions() : undefined,
          stream: true,
        };

        let fullText = '';
        let toolCalls: ToolCall[] = [];
        let hasToolCalls = false;

        for await (const chunk of this.provider.chat(this.messages, chatOpts)) {
          switch (chunk.type) {
            case 'text':
              fullText += chunk.content || '';
              callbacks?.onText?.(chunk.content || '');
              yield chunk;
              break;
            case 'tool_call':
              if (chunk.toolCall) {
                hasToolCalls = true;
                toolCalls.push({
                  id: chunk.toolCall.id || `call_${Date.now()}`,
                  type: 'function',
                  function: {
                    name: chunk.toolCall.function?.name || '',
                    arguments: chunk.toolCall.function?.arguments || '{}',
                  },
                });
                yield chunk;
              }
              break;
            case 'done':
              if (chunk.usage) this.costTracker.addUsage(chunk.usage.inputTokens, chunk.usage.outputTokens);
              break;
            case 'error':
              callbacks?.onError?.(chunk.error || 'Unknown error');
              yield chunk;
              break;
            case 'thinking':
              yield chunk;
              break;
          }
        }

        const assistantMsg: Message = { role: 'assistant', content: fullText };
        if (toolCalls.length > 0) assistantMsg.tool_calls = toolCalls;
        this.messages.push(assistantMsg);

        if (!hasToolCalls || toolCalls.length === 0) {
          yield { type: 'done' };
          break;
        }

        for (const tc of toolCalls) {
          const handler = this.tools.get(tc.function.name);
          if (!handler) {
            this.messages.push({ role: 'tool', content: JSON.stringify({ error: `Unknown tool: ${tc.function.name}` }), tool_call_id: tc.id });
            continue;
          }

          try {
            const args = JSON.parse(tc.function.arguments) as Record<string, unknown>;
            callbacks?.onToolCall?.(tc.function.name, args);
            const result = await handler.execute(args);
            callbacks?.onToolResult?.(tc.function.name, result);

            this.messages.push({ 
              role: 'tool', 
              content: result, 
              tool_call_id: tc.id 
            });
          } catch (error) {
            const errMsg = `Tool ${tc.function.name} failed: ${error}`;
            this.messages.push({ role: 'tool', content: JSON.stringify({ error: errMsg }), tool_call_id: tc.id });
            callbacks?.onError?.(errMsg);
          }
        }

        toolLoopCount++;
        toolCalls = [];
        hasToolCalls = false;
      }

      if (toolLoopCount >= this.maxToolLoops) {
        yield { type: 'error', error: `Max tool loops (${this.maxToolLoops}) reached` };
      }
    } finally {
      this.isProcessing = false;
    }
  }

  getMessages(): Message[] { return [...this.messages]; }
  setMessages(msgs: Message[]) { this.messages = msgs; }
  clearHistory() { this.messages = []; this.costTracker.reset(); }
  clone(_sessionId?: string): QueryEngine {
    const cloned = new QueryEngine({
      provider: this.provider,
      model: this.model,
      systemPrompt: this.systemPrompt,
      tools: Array.from(this.tools.values()),
      maxToolLoops: this.maxToolLoops,
      temperature: this.temperature,
      maxTokens: this.maxTokens,
    });
    cloned.setMessages(this.getMessages());
    return cloned;
  }
  getCostTracker(): CostTracker { return this.costTracker; }
  getContextCollector(): ContextCollector { return this.contextCollector; }
  setProvider(p: LLMProvider) { this.provider = p; }
  setModel(m: string) { this.model = m; this.costTracker.setModel(m); }
  getModel(): string { return this.model; }
  getProvider(): LLMProvider { return this.provider; }
  isActive(): boolean { return this.isProcessing; }
  getMessageCount(): number { return this.messages.length; }

  estimateContextTokens(): number {
    let total = estimateTokens(this.systemPrompt);
    for (const msg of this.messages) total += estimateTokens(msg.content);
    return total;
  }
}
