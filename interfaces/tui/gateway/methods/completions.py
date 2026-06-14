"""
Completion method handler — slash commands and path completions.
"""

import os
from typing import Any


SLASH_COMMANDS: dict[str, str] = {
    "help": "Show available commands and usage information",
    "new": "Start a new chat session",
    "clear": "Clear the current conversation",
    "sessions": "List and manage chat sessions",
    "config": "View or change CIEL configuration",
    "providers": "List available LLM providers",
    "model": "Switch the active model",
    "tools": "List available tools and their descriptions",
    "status": "Show CIEL system status and statistics",
    "voice": "Enter voice chat mode",
    "desktop": "Launch the desktop application",
    "update": "Check for CIEL updates",
    "export": "Export the current conversation",
    "save": "Save the current conversation to a file",
    "load": "Load a conversation from a file",
    "history": "Show command history",
}


class CompletionMethods:
    """Slash command and path completions."""

    def __init__(self, server):
        self.server = server

    def get_methods(self) -> dict[str, Any]:
        return {
            "completions.slash": self.handle_slash,
            "completions.path": self.handle_path,
        }

    async def handle_slash(self, params: dict) -> dict:
        """Return slash command completions matching the query."""
        query = params.get("query", "").lower()
        if not query:
            return {"completions": list(SLASH_COMMANDS.keys())}

        matches = []
        for cmd, desc in SLASH_COMMANDS.items():
            if cmd.startswith(query) or query in cmd:
                matches.append(f"/{cmd} — {desc}")

        return {"completions": matches}

    async def handle_path(self, params: dict) -> dict:
        """Return file path completions."""
        query = params.get("query", "")
        cwd = params.get("cwd") or os.getcwd()

        if not query:
            return {"completions": []}

        # Determine the base directory and prefix
        if query.endswith("/"):
            base_dir = os.path.join(cwd, query) if not os.path.isabs(query) else query
            prefix = ""
        else:
            base_dir = os.path.dirname(os.path.join(cwd, query))
            prefix = os.path.basename(query)

        if not os.path.isdir(base_dir):
            return {"completions": []}

        try:
            entries = os.listdir(base_dir)
            matches = []
            for entry in entries:
                if entry.startswith(prefix):
                    full = os.path.join(base_dir, entry)
                    if os.path.isdir(full):
                        matches.append(entry + "/")
                    else:
                        matches.append(entry)
            matches.sort()
            return {"completions": matches[:20]}  # Limit to 20 results
        except PermissionError:
            return {"completions": []}
