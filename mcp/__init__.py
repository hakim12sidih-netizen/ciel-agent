"""
CIEL v1.0 — MCP : Model Context Protocol.

Serveur MCP exposant les outils CIEL comme outils MCP,
utilisable depuis Claude Desktop, Cursor, etc.
"""
from __future__ import annotations
from ciel.mcp.server import MCPServer

__all__ = ["MCPServer"]
