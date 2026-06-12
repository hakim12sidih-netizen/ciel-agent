/**
 * CIEL v1.0 — Plugin SDK (TypeScript)
 *
 * SDK for building CIEL plugins in TypeScript.
 * Mirrors the Python plugin architecture for polyglot plugins.
 */

export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  entry: string;
  description?: string;
  channels?: string[];
  providers?: string[];
  tools?: string[];
  hooks?: string[];
  minHostVersion?: string;
}

export interface PluginAPI {
  pluginId: string;
  registerHook(event: string, handler: (...args: unknown[]) => unknown): void;
  registerTool(name: string, handler: (...args: unknown[]) => unknown, description?: string): void;
  registerChannel(channelId: string, adapter: unknown): void;
  registerProvider(providerId: string, config: Record<string, unknown>): void;
  on(event: string, handler: (...args: unknown[]) => unknown): void;
}

export function createPluginAPI(pluginId: string): PluginAPI {
  const hooks = new Map<string, Array<(...args: unknown[]) => unknown>>();
  const tools = new Map<string, (...args: unknown[]) => unknown>();

  return {
    pluginId,
    registerHook(event: string, handler: (...args: unknown[]) => unknown) {
      if (!hooks.has(event)) hooks.set(event, []);
      hooks.get(event)!.push(handler);
    },
    registerTool(name: string, handler: (...args: unknown[]) => unknown, _description?: string) {
      tools.set(name, handler);
    },
    registerChannel(_channelId: string, _adapter: unknown) {
      // Channel registration
    },
    registerProvider(_providerId: string, _config: Record<string, unknown>) {
      // Provider registration
    },
    on(event: string, handler: (...args: unknown[]) => unknown) {
      this.registerHook(event, handler);
    },
  };
}

export function definePlugin(manifest: PluginManifest, registerFn: (api: PluginAPI) => void) {
  return { manifest, register: registerFn };
}
