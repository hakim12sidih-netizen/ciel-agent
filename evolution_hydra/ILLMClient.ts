/**
 * ═══════════════════════════════════════════════════════════════
 * I-LLM-CLIENT — Abstraction minimale pour LLM
 * ═══════════════════════════════════════════════════════════════
 *
 * Pas besoin de recréer un provider complet : LLMTransmuter veut
 * juste `complete(prompt) → text`. On abstrait cette seule méthode
 * pour pouvoir mocker le LLM dans les tests.
 *
 * Si un LLMProvider complet (GroqProvider, OllamaProvider, etc.)
 * est disponible, on l'enveloppe via `wrapProvider()`.
 */

import type { Message, StreamChunk } from '../providers/Provider.js';

export interface LLMCompletionOptions {
  maxTokens?: number;
  temperature?: number;
  systemPrompt?: string;
  stopSequences?: string[];
}

export interface ILLMClient {
  readonly name: string;
  /**
   * Envoie un prompt et récupère la réponse texte complète.
   * Le client abstrait l'AsyncGenerator<StreamChunk> des LLMProvider
   * concrets en une simple Promise<string>.
   */
  complete(prompt: string, options?: LLMCompletionOptions): Promise<string>;

  /**
   * Variante "stop sequences" : arrête la génération à l'un des motifs.
   * Utile pour les LLM qui bavardent après le code.
   */
  completeWithStop?(
    prompt: string,
    stopSequences: string[],
    options?: LLMCompletionOptions
  ): Promise<string>;

  /** Le client est-il disponible (clé API, modèle chargé, etc.) ? */
  isAvailable(): Promise<boolean>;
}

/**
 * Wrapper optionnel pour transformer un LLMProvider en ILLMClient.
 * L'import est dynamique pour éviter de casser le graphe de modules.
 */
export async function wrapProvider(
  provider: {
    chat: (msgs: Message[], opts?: Record<string, unknown>) => AsyncGenerator<StreamChunk>;
    name: string;
    isAvailable: () => Promise<boolean>;
  }
): Promise<ILLMClient> {
  return {
    name: provider.name,
    isAvailable: () => provider.isAvailable(),
    async complete(prompt: string, options: LLMCompletionOptions = {}): Promise<string> {
      const messages = options.systemPrompt
        ? [
            { role: 'system' as const, content: options.systemPrompt },
            { role: 'user' as const, content: prompt },
          ]
        : [{ role: 'user' as const, content: prompt }];

      let full = '';
      for await (const chunk of provider.chat(messages, {
        maxTokens: options.maxTokens ?? 4096,
        temperature: options.temperature ?? 0.3,
      })) {
        if (chunk.type === 'text' && chunk.content) {
          full += chunk.content;
        } else if (chunk.type === 'error') {
          throw new Error(`LLM error: ${chunk.error ?? 'unknown'}`);
        }
      }
      return full;
    },
  };
}

/**
 * MockLLMClient pour les tests et le mode offline.
 * Répond des textes pré-enregistrés en fonction du prompt.
 */
export class MockLLMClient implements ILLMClient {
  public readonly name = 'mock';
  private responses: Array<{ match: RegExp | string; response: string }> = [];
  private callLog: Array<{ prompt: string; options?: LLMCompletionOptions }> = [];
  private failQueue: string[] = [];

  /** Répond `text` à tout prompt contenant `match`. */
  public onPrompt(match: RegExp | string, text: string): this {
    this.responses.push({ match, response: text });
    return this;
  }

  /** Prochaine invocation throw une erreur avec ce message. */
  public failOnce(message = 'mock LLM error'): this {
    this.failQueue.push(message);
    return this;
  }

  public async complete(prompt: string, options?: LLMCompletionOptions): Promise<string> {
    this.callLog.push({ prompt, options });
    if (this.failQueue.length > 0) {
      const msg = this.failQueue.shift()!;
      throw new Error(msg);
    }
    for (const r of this.responses) {
      if (typeof r.match === 'string') {
        if (prompt.includes(r.match)) return r.response;
      } else {
        if (r.match.test(prompt)) return r.response;
      }
    }
    return '// no mock response configured\n';
  }

  public async isAvailable(): Promise<boolean> {
    return true;
  }

  /** Historique des appels (debug / tests). */
  public getCalls(): Array<{ prompt: string; options?: LLMCompletionOptions }> {
    return [...this.callLog];
  }
}
