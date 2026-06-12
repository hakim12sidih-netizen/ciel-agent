/**
 * CIEL Polyglot Bridge — TypeScript ↔ Python/Go/Rust
 *
 * Provides a unified interface for calling into Python and Go modules
 * from the TypeScript core. Uses subprocess JSON-RPC for Python
 * and direct HTTP for Go.
 */
import { spawn, type ChildProcess } from "child_process";
import { resolve } from "path";

interface RPCRequest {
  jsonrpc: "2.0";
  method: string;
  params: unknown[];
  id: number;
}

interface RPCResponse {
  jsonrpc: "2.0";
  result?: unknown;
  error?: { code: number; message: string };
  id: number;
}

export class PolyglotBridge {
  private pythonProcess: ChildProcess | null = null;
  private requestId = 0;
  private pending = new Map<number, { resolve: (v: unknown) => void; reject: (e: Error) => void }>();
  private buffer = "";

  async connect(): Promise<void> {
    const pythonScript = resolve(import.meta.dir, "../../../bridge/py_bridge.py");
    this.pythonProcess = spawn("python3", [pythonScript], {
      stdio: ["pipe", "pipe", "pipe"],
    });

    this.pythonProcess.stdout!.on("data", (data: Buffer) => {
      this.buffer += data.toString();
      this.processBuffer();
    });

    this.pythonProcess.on("exit", (code) => {
      console.error(`Python bridge exited with code ${code}`);
      this.pythonProcess = null;
    });

    // Wait for ready signal
    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error("Bridge timeout")), 5000);
      const check = (data: Buffer) => {
        if (data.toString().includes("CIEL_BRIDGE_READY")) {
          clearTimeout(timeout);
          this.pythonProcess!.stdout!.removeListener("data", check);
          resolve();
        }
      };
      this.pythonProcess!.stdout!.on("data", check);
    });
  }

  async disconnect(): Promise<void> {
    if (this.pythonProcess) {
      this.pythonProcess.kill();
      this.pythonProcess = null;
    }
  }

  async call(method: string, ...params: unknown[]): Promise<unknown> {
    if (!this.pythonProcess) {
      throw new Error("Bridge not connected. Call connect() first.");
    }

    const id = ++this.requestId;
    const request: RPCRequest = {
      jsonrpc: "2.0",
      method,
      params,
      id,
    };

    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.pythonProcess!.stdin!.write(JSON.stringify(request) + "\n");
    });
  }

  private processBuffer(): void {
    const lines = this.buffer.split("\n");
    this.buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const response: RPCResponse = JSON.parse(line);
        const pending = this.pending.get(response.id);
        if (pending) {
          this.pending.delete(response.id);
          if (response.error) {
            pending.reject(new Error(response.error.message));
          } else {
            pending.resolve(response.result);
          }
        }
      } catch (e) {
        console.error("Failed to parse bridge response:", line, e);
      }
    }
  }

  isConnected(): boolean {
    return this.pythonProcess !== null && this.pythonProcess.exitCode === null;
  }
}
