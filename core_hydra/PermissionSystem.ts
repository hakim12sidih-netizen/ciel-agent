export enum PermissionState {
  ALLOW = 'allow',
  DENY = 'deny',
  ASK = 'ask'
}

export class PermissionSystem {
  private mode: 'default' | 'auto' | 'strict';
  private allowedTools: Set<string>;
  private deniedTools: Set<string>;

  constructor(opts: { mode?: 'default' | 'auto' | 'strict'; allowedTools?: string[]; deniedTools?: string[] } = {}) {
    this.mode = opts.mode || 'default';
    this.allowedTools = new Set(opts.allowedTools || []);
    this.deniedTools = new Set(opts.deniedTools || []);
  }

  check(toolName: string, isSafe: boolean): PermissionState {
    if (this.deniedTools.has(toolName)) return PermissionState.DENY;
    if (this.allowedTools.has(toolName)) return PermissionState.ALLOW;

    if (this.mode === 'auto') return PermissionState.ALLOW;
    if (this.mode === 'strict') return PermissionState.ASK;
    
    // default mode
    return isSafe ? PermissionState.ALLOW : PermissionState.ASK;
  }

  allow(toolName: string) { this.allowedTools.add(toolName); }
  deny(toolName: string) { this.deniedTools.add(toolName); }
}
