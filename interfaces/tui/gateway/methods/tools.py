"""
Tool method handler — list and execute CIEL tools.
Uses ToolForgeEngine.run() for execution, plus MCP and cognition tool dispatch.
"""

import time
from typing import Any


_tool_forge = None

def _get_tool_forge():
    global _tool_forge
    if _tool_forge is None:
        from ciel.toolforge.core import ToolForgeEngine
        _tool_forge = ToolForgeEngine()
    return _tool_forge


def _get_brain():
    from ciel.brain.core import CIELBrain
    return CIELBrain()


TOOL_DEFS: dict[str, dict] = {
    "bash": {
        "name": "bash",
        "description": "Execute a bash command in the shell",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to execute"},
                "description": {"type": "string", "description": "Brief description of the command"},
                "timeout": {"type": "number", "description": "Timeout in milliseconds"},
            },
            "required": ["command", "description"],
        },
        "toolset": "builtin",
        "requiresApproval": True,
    },
    "read": {
        "name": "read",
        "description": "Read a file from the filesystem",
        "parameters": {
            "type": "object",
            "properties": {
                "filePath": {"type": "string", "description": "Absolute path to the file"},
                "offset": {"type": "number", "description": "Line number to start from"},
                "limit": {"type": "number", "description": "Maximum lines to read"},
            },
            "required": ["filePath"],
        },
        "toolset": "builtin",
        "requiresApproval": False,
    },
    "write": {
        "name": "write",
        "description": "Write content to a file",
        "parameters": {
            "type": "object",
            "properties": {
                "filePath": {"type": "string", "description": "Absolute path to the file"},
                "content": {"type": "string", "description": "File content"},
            },
            "required": ["filePath", "content"],
        },
        "toolset": "builtin",
        "requiresApproval": True,
    },
    "glob": {
        "name": "glob",
        "description": "Find files by name patterns",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern"},
                "path": {"type": "string", "description": "Directory to search"},
            },
            "required": ["pattern"],
        },
        "toolset": "builtin",
        "requiresApproval": False,
    },
    "grep": {
        "name": "grep",
        "description": "Search file contents using regular expressions",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern"},
                "path": {"type": "string", "description": "Directory to search"},
                "include": {"type": "string", "description": "File pattern filter"},
            },
            "required": ["pattern"],
        },
        "toolset": "builtin",
        "requiresApproval": False,
    },
    "web_search": {
        "name": "web_search",
        "description": "Search the web for information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "numResults": {"type": "number", "description": "Number of results"},
            },
            "required": ["query"],
        },
        "toolset": "builtin",
        "requiresApproval": False,
    },
    "web_fetch": {
        "name": "web_fetch",
        "description": "Fetch and read a URL",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "format": {"type": "string", "description": "Output format (markdown, text, html)"},
            },
            "required": ["url"],
        },
        "toolset": "builtin",
        "requiresApproval": False,
    },
    "edit": {
        "name": "edit",
        "description": "Edit a file by replacing text",
        "parameters": {
            "type": "object",
            "properties": {
                "filePath": {"type": "string", "description": "Absolute path to the file"},
                "oldString": {"type": "string", "description": "Text to replace"},
                "newString": {"type": "string", "description": "Replacement text"},
            },
            "required": ["filePath", "oldString", "newString"],
        },
        "toolset": "builtin",
        "requiresApproval": True,
    },
    "ask": {
        "name": "ask",
        "description": "Ask the user a question",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Question to ask"},
                "options": {"type": "array", "items": {"type": "string"}, "description": "Answer options"},
            },
            "required": ["question"],
        },
        "toolset": "builtin",
        "requiresApproval": False,
    },
    "mcp": {
        "name": "mcp",
        "description": "Make a tool call via MCP (Model Context Protocol)",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "MCP tool name"},
                "arguments": {"type": "object", "description": "Tool arguments"},
            },
            "required": ["name", "arguments"],
        },
        "toolset": "builtin",
        "requiresApproval": True,
    },
    "sandbox": {
        "name": "sandbox",
        "description": "Execute code in sandboxed environment",
        "parameters": {
            "type": "object",
            "properties": {
                "language": {"type": "string", "description": "Language (python, javascript, etc)"},
                "code": {"type": "string", "description": "Code to execute"},
            },
            "required": ["language", "code"],
        },
        "toolset": "builtin",
        "requiresApproval": True,
    },
}


class ToolMethods:

    def __init__(self, server):
        self.server = server

    def get_methods(self) -> dict[str, Any]:
        return {
            "tools.list": self.handle_list,
            "tools.execute": self.handle_execute,
        }

    async def handle_list(self, params: dict) -> dict:
        tools = dict(TOOL_DEFS)

        # Add registered tools from the API tool registry
        try:
            from ciel.api.tool_registry import get_tool_list
            for entry in get_tool_list():
                tid = entry.get("id", "")
                if tid and tid not in tools:
                    tools[tid] = {
                        "name": tid,
                        "description": entry.get("description", ""),
                        "parameters": entry.get("parameters", {}),
                        "toolset": entry.get("category", "registered"),
                        "requiresApproval": entry.get("requires_approval", True),
                    }
        except (ImportError, AttributeError):
            pass

        # Add MCP tools
        try:
            from ciel.interfaces.mcp_server import TOOLS as mcp_tools
            for t_def in mcp_tools:
                name = t_def.get("name", "")
                if name and name not in tools:
                    tools[name] = {
                        "name": name,
                        "description": t_def.get("description", ""),
                        "parameters": t_def.get("inputSchema", t_def.get("parameters", {})),
                        "toolset": "mcp",
                        "requiresApproval": True,
                    }
        except (ImportError, AttributeError):
            pass

        return {"tools": list(tools.values())}

    async def handle_execute(self, params: dict) -> dict:
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        start = time.time()

        def _err(msg: str) -> dict:
            return {"success": False, "error": msg, "duration": time.time() - start}

        try:
            await self.server.emitter.tool_progress(name, 0, f"Starting {name}...")

            # Builtin tools — use cognition _execute_tool logic
            if name in TOOL_DEFS:
                result = await self._execute_builtin(name, arguments)
            else:
                # Try ToolForge first
                forge = _get_tool_forge()
                tool_result = forge.run(name, **arguments)
                if isinstance(tool_result, dict) and "error" in tool_result:
                    raise ValueError(tool_result["error"])
                result = tool_result

            duration = time.time() - start
            await self.server.emitter.tool_progress(name, 100, f"{name} completed in {duration:.2f}s")
            return {
                "success": True,
                "result": str(result) if result is not None else "",
                "duration": duration,
            }

        except ValueError as e:
            duration = time.time() - start
            await self.server.emitter.tool_progress(name, 100, f"{name} failed: {e}")
            return {"success": False, "error": str(e), "duration": duration}
        except Exception as e:
            duration = time.time() - start
            await self.server.emitter.tool_progress(name, 100, f"{name} failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e), "duration": duration}

    async def _execute_builtin(self, name: str, args: dict) -> str:
        """Execute a builtin tool via cognition API."""
        from ciel.api.routes.cognition import _execute_tool
        brain = _get_brain()
        result = await _execute_tool(name, args, brain=brain)
        return result.get("output", str(result))
