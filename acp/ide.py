from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


VSCODE_EXTENSION_MANIFEST = {
    "name": "ciel-acp",
    "displayName": "CIEL ACP — Agent Cognitif dans l'IDE",
    "description": "Agent CIEL intégré à VS Code via ACP. Analyse de code, suggestions, refactoring, chat IA.",
    "version": "1.0.0",
    "publisher": "ciel",
    "engines": {"vscode": "^1.90.0"},
    "categories": ["Programming Languages", "Other"],
    "activationEvents": ["onStartupFinished"],
    "main": "./out/extension.js",
    "contributes": {
        "commands": [
            {
                "command": "ciel.openChat",
                "title": "CIEL: Ouvrir le chat",
                "icon": "$(comment-discussion)",
            },
            {
                "command": "ciel.analyzeFile",
                "title": "CIEL: Analyser le fichier actif",
                "icon": "$(sparkle)",
            },
            {
                "command": "ciel.suggestRefactor",
                "title": "CIEL: Suggérer des refactorisations",
                "icon": "$(lightbulb)",
            },
            {
                "command": "ciel.searchCode",
                "title": "CIEL: Rechercher dans le code",
                "icon": "$(search)",
            },
            {
                "command": "ciel.toggleDiagnostics",
                "title": "CIEL: Activer/désactiver les diagnostics en direct",
                "icon": "$(bug)",
            },
        ],
        "keybindings": [
            {"command": "ciel.openChat", "key": "ctrl+shift+c", "mac": "cmd+shift+c"},
            {"command": "ciel.analyzeFile", "key": "ctrl+shift+a", "mac": "cmd+shift+a"},
        ],
        "configuration": {
            "title": "CIEL ACP",
            "properties": {
                "ciel.acp.host": {
                    "type": "string",
                    "default": "127.0.0.1",
                    "description": "Hôte du serveur ACP CIEL",
                },
                "ciel.acp.port": {
                    "type": "number",
                    "default": 9876,
                    "description": "Port WebSocket du serveur ACP CIEL",
                },
                "ciel.api.key": {
                    "type": "string",
                    "default": "",
                    "description": "Clé API CIEL (optionnelle)",
                },
            },
        },
    },
}


CURSOR_RULES = """# CIEL Agent — Règles de Collaboration

Tu es CIEL, un agent cognitif intégré à l'IDE. Tu assistes le développeur
en analysant le code, en suggérant des améliorations, et en exécutant
des tâches via le protocole ACP.

## Comportement Général
- Sois proactif: signale les problèmes potentiels sans attendre qu'on te les demande.
- Reste concis: préfère des suggestions courtes et actionnables.
- Connais le projet: utilise ACP pour explorer la codebase avant de répondre.
- Suggère des refactorisations quand tu vois de la duplication ou de la complexité.

## Capacités (via ACP)
- `analyze_code` : Analyse un fichier (syntaxe, style, patterns).
- `search_code` : Recherche dans le code par pattern.
- `read_file` / `write_file` : Lecture et écriture de fichiers.
- `run_command` : Exécution de commandes shell.
- `diagnose_file` : Diagnostics avancés (lint, imports, style).
- `suggest_refactor` : Suggestions de refactorisation.
- `ciel_chat` : Conversation avec le modèle LLM de CIEL.
- `ciel_memory_store/query` : Mémoire persistante.
- `ciel_web_search` : Recherche web.

## Workflows Recommandés

### Analyse de Code
1. À l'ouverture d'un fichier, exécute `diagnose_file` en arrière-plan.
2. Si des problèmes sont détectés, affiche-les comme diagnostics dans l'IDE.
3. Pour les problèmes complexes, propose `suggest_refactor`.

### Résolution de Bug
1. Lis le fichier signalé avec `read_file`.
2. Analyse avec `search_code` pour trouver les dépendances.
3. Diagnostique avec `diagnose_file`.
4. Propose une solution et, si approuvé, applique avec `write_file`.

### Recherche
1. Utilise `search_code` pour trouver les patterns pertinents.
2. Combine avec `read_file` pour comprendre le contexte.
3. Synthétise les résultats.

## Règles de Sécurité
- Ne jamais exécuter de commandes destructrices sans confirmation.
- Vérifier les chemins de fichiers avant écriture.
- Respecter les permissions et la configuration du projet.
"""


CURSOR_AGENT_DEFINITION = """You are CIEL, an advanced cognitive agent integrated into the IDE via ACP.
You have access to code analysis, search, file operations, and CIEL's LLM capabilities.

Use ACP tools to understand the codebase before answering questions.
Be proactive in suggesting improvements and fixing issues.
"""


VSCODE_EXTENSION_SRC = r"""import * as vscode from 'vscode';
import { ACPClient } from './acpClient';
import { CielChatPanel } from './panel';

let acpClient: ACPClient | undefined;

export function activate(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('ciel.acp');
    const host = config.get<string>('host', '127.0.0.1');
    const port = config.get<number>('port', 9876);

    acpClient = new ACPClient(`ws://${host}:${port}`);
    acpClient.connect().catch(() => {
        vscode.window.showWarningMessage('CIEL ACP: Serveur non joignable');
    });

    context.subscriptions.push(
        vscode.commands.registerCommand('ciel.openChat', () => {
            CielChatPanel.createOrShow(context.extensionUri, acpClient!);
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ciel.analyzeFile', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;
            const path = editor.document.uri.fsPath;
            if (!acpClient) return;
            const result = await acpClient.callTool('analyze_code', { file_path: path });
            vscode.window.showInformationMessage('Analyse terminée');
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ciel.suggestRefactor', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;
            const path = editor.document.uri.fsPath;
            if (!acpClient) return;
            const result = await acpClient.callTool('suggest_refactor', { file_path: path });
            // Afficher les suggestions
        }),
    );
}

export function deactivate() {
    acpClient?.disconnect();
}
"""

VSCODE_ACP_CLIENT_SRC = r"""import * as vscode from 'vscode';

export class ACPClient {
    private ws: WebSocket | undefined;
    private pending: Map<number, { resolve: Function; reject: Function }> = new Map();
    private msgId = 0;

    constructor(private url: string) {}

    async connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(this.url);
            this.ws.onopen = () => {
                this.send('initialize', {}).then(() => resolve());
            };
            this.ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.id !== undefined && this.pending.has(msg.id)) {
                    const { resolve, reject } = this.pending.get(msg.id)!;
                    this.pending.delete(msg.id);
                    if (msg.error) reject(msg.error);
                    else resolve(msg.result);
                }
            };
            this.ws.onerror = reject;
        });
    }

    disconnect(): void {
        this.ws?.close();
    }

    async callTool(name: string, arguments: Record<string, any>): Promise<any> {
        return this.send('acp/tools/call', { name, arguments });
    }

    async listTools(): Promise<any> {
        return this.send('acp/tools/list', {});
    }

    private send(method: string, params: any): Promise<any> {
        return new Promise((resolve, reject) => {
            const id = ++this.msgId;
            this.pending.set(id, { resolve, reject });
            this.ws?.send(JSON.stringify({
                jsonrpc: '2.0', id, method, params,
            }));
        });
    }
}
"""

VSCODE_PANEL_SRC = r"""import * as vscode from 'vscode';
import { ACPClient } from './acpClient';

export class CielChatPanel {
    public static currentPanel: CielChatPanel | undefined;
    private panel: vscode.WebviewPanel;

    static createOrShow(extensionUri: vscode.Uri, client: ACPClient) {
        if (CielChatPanel.currentPanel) {
            CielChatPanel.currentPanel.panel.reveal();
            return;
        }
        const panel = vscode.window.createWebviewPanel(
            'cielChat', 'CIEL Chat',
            vscode.ViewColumn.Beside,
            { enableScripts: true },
        );
        panel.webview.html = this._getHtml();
        CielChatPanel.currentPanel = new CielChatPanel(panel, client);
    }

    private constructor(panel: vscode.WebviewPanel, private client: ACPClient) {
        this.panel = panel;
        panel.onDidDispose(() => { CielChatPanel.currentPanel = undefined; });
    }

    private static _getHtml(): string {
        return `<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>CIEL Chat</title>
<style>
body { font-family: system-ui; padding: 16px; }
#messages { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 8px; margin-bottom: 8px; }
input { width: 100%; padding: 8px; box-sizing: border-box; }
.message { margin: 4px 0; padding: 4px 8px; border-radius: 4px; }
.user { background: #e3f2fd; }
.assistant { background: #f3e5f5; }
</style></head>
<body>
<div id="messages"></div>
<input id="input" placeholder="Message pour CIEL..." />
<script>
const vscode = acquireVsCodeApi();
const input = document.getElementById('input');
input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && input.value) {
        vscode.postMessage({ type: 'chat', text: input.value });
        input.value = '';
    }
});
</script>
</body></html>`;
    }
}
"""


def generate_vscode_extension(target_dir: str) -> dict[str, str]:
    files = {
        "package.json": json.dumps(VSCODE_EXTENSION_MANIFEST, indent=2),
        "src/extension.ts": VSCODE_EXTENSION_SRC,
        "src/acpClient.ts": VSCODE_ACP_CLIENT_SRC,
        "src/panel.ts": VSCODE_PANEL_SRC,
        "tsconfig.json": json.dumps({
            "compilerOptions": {
                "module": "commonjs",
                "target": "ES2022",
                "outDir": "out",
                "rootDir": "src",
                "sourceMap": True,
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
            },
            "include": ["src"],
            "exclude": ["node_modules", "out"],
        }, indent=2),
    }
    for filepath, content in files.items():
        p = Path(target_dir) / filepath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return files


def generate_cursor_rules(target_dir: str) -> None:
    p = Path(target_dir) / ".cursorrules"
    p.write_text(CURSOR_RULES)
    agent_dir = Path(target_dir) / ".cursor" / "rules"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "ciel-agent.mdc").write_text(
        f"---\ndescription: CIEL Agent rules for ACP integration\nglobs: **/*\n---\n\n{CURSOR_AGENT_DEFINITION}"
    )
