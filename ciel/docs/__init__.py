"""
CIEL — Documentation Generator.

Generate auto-documentation for CIEL modules:
  - Mesh distribué (gRPC+QUIC)
  - ACP / IDE integration
  - Terminal backends
  - Themes

Usage:
    ciel docs generate [--output-dir docs/] [--modules mesh,acp,interfaces]
"""
from __future__ import annotations

from .generator import generate_all, generate_module_doc, write_docs

__all__ = ["generate_all", "generate_module_doc", "write_docs"]
