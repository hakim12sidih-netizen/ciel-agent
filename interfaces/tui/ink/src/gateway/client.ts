import type {
  GatewayConnectionState,
  JSONRPCRequest,
  JSONRPCResponse,
  GatewayEvent,
  SkinConfig,
} from '../types';

interface PendingRequest {
  resolve: (result: unknown) => void;
  reject: (error: Error) => void;
  timer: ReturnType<typeof setTimeout>;
}

export class GatewayClient {
  private proc: Deno.Command | null = null;
  private process: Deno.ChildProcess | null = null;
  private stdin: WritableStream<Uint8Array> | null = null;
  private reader: ReadableStreamDefaultReader<Uint8Array> | null = null;
  private buffer = '';
  private requestId = 0;
  private pending = new Map<string | number, PendingRequest>();
  private eventHandlers = new Map<string, Set<(event: GatewayEvent) => void>>();

  state: GatewayConnectionState = {
    connected: false,
    connecting: false,
    error: null,
    capabilities: [],
    skin: null,
  };

  private onStateChange: ((state: GatewayConnectionState) => void) | null = null;

  setStateChangeHandler(handler: (state: GatewayConnectionState) => void) {
    this.onStateChange = handler;
  }

  private updateState(partial: Partial<GatewayConnectionState>) {
    this.state = { ...this.state, ...partial };
    this.onStateChange?.(this.state);
  }

  async connect(pythonPath = 'python3', cwd?: string): Promise<void> {
    if (this.state.connected || this.state.connecting) return;
    this.updateState({ connecting: true, error: null });

    try {
      const cmd = new Deno.Command(pythonPath, {
        args: ['-m', 'ciel.interfaces.tui.gateway.server'],
        cwd,
        stdin: 'piped',
        stdout: 'piped',
        stderr: 'piped',
      });

      this.proc = cmd;
      this.process = cmd.spawn();
      this.stdin = this.process.stdin;
      this.reader = this.process.stdout.getReader();
      this.updateState({ connected: true, connecting: false });

      // Read stderr for diagnostics
      const stderrReader = this.process.stderr.getReader();
      this.readStderr(stderrReader);

      // Read stdout for JSON-RPC messages
      this.readStdout();

      // Wait for gateway.ready event
      await this.waitForReady(5000);
    } catch (err) {
      this.updateState({
        connected: false,
        connecting: false,
        error: `Connection failed: ${(err as Error).message}`,
      });
      throw err;
    }
  }

  private async readStderr(reader: ReadableStreamDefaultReader<Uint8Array>) {
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      console.error('[gateway:stderr]', decoder.decode(value));
    }
  }

  private async readStdout() {
    const decoder = new TextDecoder();
    while (this.reader) {
      const { done, value } = await this.reader.read();
      if (done) {
        this.updateState({ connected: false, error: 'Gateway process exited' });
        break;
      }
      this.buffer += decoder.decode(value, { stream: true });
      this.processBuffer();
    }
  }

  private processBuffer() {
    let newlineIdx: number;
    while ((newlineIdx = this.buffer.indexOf('\n')) !== -1) {
      const line = this.buffer.slice(0, newlineIdx).trim();
      this.buffer = this.buffer.slice(newlineIdx + 1);
      if (!line) continue;
      try {
        const msg = JSON.parse(line);
        this.handleMessage(msg);
      } catch {
        console.warn('[gateway] Invalid JSON:', line);
      }
    }
  }

  private handleMessage(msg: JSONRPCResponse | GatewayEvent) {
    if ('method' in msg && !('id' in msg)) {
      // Notification/event
      const event = msg as GatewayEvent;
      const handlers = this.eventHandlers.get((event as any).method || event.type);
      if (handlers) {
        handlers.forEach((h) => h(event));
      }
      return;
    }

    // Response
    const response = msg as JSONRPCResponse;
    const pending = this.pending.get(response.id);
    if (pending) {
      clearTimeout(pending.timer);
      this.pending.delete(response.id);
      if (response.error) {
        pending.reject(new Error(response.error.message));
      } else {
        pending.resolve(response.result);
      }
    }
  }

  private waitForReady(timeout: number): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.state.skin) {
        resolve();
        return;
      }

      const timer = setTimeout(() => {
        this.off('gateway.ready', handler);
        reject(new Error('Gateway not ready within timeout'));
      }, timeout);

      const handler = (event: GatewayEvent) => {
        if (event.type === 'gateway.ready') {
          clearTimeout(timer);
          this.updateState({
            skin: event.skin,
            capabilities: event.capabilities,
          });
          resolve();
        }
      };

      this.on('gateway.ready', handler);
    });
  }

  async request<T = unknown>(method: string, params?: Record<string, unknown>): Promise<T> {
    const id = ++this.requestId;
    const request: JSONRPCRequest = {
      jsonrpc: '2.0',
      id,
      method,
      params,
    };

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Request ${method} timed out`));
      }, 30000);

      this.pending.set(id, { resolve, reject, timer });

      if (this.stdin) {
        const writer = this.stdin.getWriter();
        writer.write(new TextEncoder().encode(JSON.stringify(request) + '\n'));
        writer.releaseLock();
      } else {
        clearTimeout(timer);
        this.pending.delete(id);
        reject(new Error('Gateway not connected'));
      }
    });
  }

  async *stream<T = unknown>(method: string, params?: Record<string, unknown>): AsyncGenerator<T> {
    const id = ++this.requestId;
    const request: JSONRPCRequest = {
      jsonrpc: '2.0',
      id,
      method,
      params: { ...params, stream: true },
    };

    if (!this.stdin) throw new Error('Gateway not connected');

    const writer = this.stdin.getWriter();
    await writer.write(new TextEncoder().encode(JSON.stringify(request) + '\n'));
    writer.releaseLock();
  }

  on(type: string, handler: (event: GatewayEvent) => void): () => void {
    if (!this.eventHandlers.has(type)) {
      this.eventHandlers.set(type, new Set());
    }
    this.eventHandlers.get(type)!.add(handler);
    return () => {
      this.eventHandlers.get(type)?.delete(handler);
    };
  }

  off(type: string, handler: (event: GatewayEvent) => void): void {
    this.eventHandlers.get(type)?.delete(handler);
  }

  getSkin(): SkinConfig | null {
    return this.state.skin;
  }

  async disconnect(): Promise<void> {
    this.reader?.cancel();
    this.process?.kill('SIGTERM');
    this.updateState({ connected: false, skin: null, capabilities: [] });
    this.pending.forEach((p) => {
      clearTimeout(p.timer);
      p.reject(new Error('Gateway disconnected'));
    });
    this.pending.clear();
  }
}

export const gateway = new GatewayClient();
