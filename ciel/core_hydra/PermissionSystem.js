export var PermissionState;
(function (PermissionState) {
    PermissionState["ALLOW"] = "allow";
    PermissionState["DENY"] = "deny";
    PermissionState["ASK"] = "ask";
})(PermissionState || (PermissionState = {}));
export class PermissionSystem {
    mode;
    allowedTools;
    deniedTools;
    constructor(opts = {}) {
        this.mode = opts.mode || 'default';
        this.allowedTools = new Set(opts.allowedTools || []);
        this.deniedTools = new Set(opts.deniedTools || []);
    }
    check(toolName, isSafe) {
        if (this.deniedTools.has(toolName))
            return PermissionState.DENY;
        if (this.allowedTools.has(toolName))
            return PermissionState.ALLOW;
        if (this.mode === 'auto')
            return PermissionState.ALLOW;
        if (this.mode === 'strict')
            return PermissionState.ASK;
        // default mode
        return isSafe ? PermissionState.ALLOW : PermissionState.ASK;
    }
    allow(toolName) { this.allowedTools.add(toolName); }
    deny(toolName) { this.deniedTools.add(toolName); }
}
