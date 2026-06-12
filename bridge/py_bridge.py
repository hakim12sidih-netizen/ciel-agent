#!/usr/bin/env python3
"""
CIEL Polyglot Bridge — Python side.
JSON-RPC 2.0 over stdio.

Connects CIEL's Python modules (core, evolution, ethics, agents)
to the TypeScript TUI and Go/Rust modules.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def import_module(name: str):
    """Lazy import a CIEL module."""
    import importlib
    return importlib.import_module(name)


ROUTER: dict[str, callable] = {}


def route(method: str):
    """Decorator to register a JSON-RPC method."""
    def decorator(fn):
        ROUTER[method] = fn
        return fn
    return decorator


# ── Registered methods ──────────────────────────────────

@route("kernel.health")
def kernel_health(params: list) -> dict:
    from ciel.core.kernel import Kernel, KernelConfig
    import asyncio
    async def _health() -> dict:
        cfg = KernelConfig(tick_interval_ms=10, max_ticks=5, enable_metrics=True)
        async with Kernel(root=ROOT, identity_dir=ROOT / "data" / "identity", config=cfg) as k:
            async for tick in k.run(duration_s=0.5):
                pass
        return k.health()
    return asyncio.run(_health())


@route("evolution.run")
def evolution_run(params: list) -> dict:
    from ciel.evolution.unified_genome import UnifiedGenome
    from ciel.evolution.imperial_cycle import ImperialCycle
    from ciel.evolution.fitness_evaluator import FitnessEvaluator

    generations = params[0] if params else 10
    genome = UnifiedGenome(genome_id="CIEL-GENESIS", mode="v2")
    evaluator = FitnessEvaluator()
    cycle = ImperialCycle(genome=genome, evaluator=evaluator)

    results = []
    for i in range(generations):
        result = cycle.run_generation()
        results.append(result.to_dict())

    return {
        "generations": generations,
        "final_fitness": results[-1]["fitness"] if results else 0,
        "genome_id": genome.id,
        "results": results,
    }


@route("evolution.genome")
def evolution_genome(params: list) -> dict:
    from ciel.evolution.unified_genome import UnifiedGenome
    mode = params[0] if params else "v2"
    g = UnifiedGenome(genome_id=f"CIEL-{mode.upper()}", mode=mode)
    return g.to_dict()


@route("identity.info")
def identity_info(params: list) -> dict:
    from ciel.core.identity import exists, load
    identity_dir = ROOT / "data" / "identity"
    if not exists(identity_dir):
        return {"status": "not_initialized"}
    identity = load(identity_dir)
    return {
        "uuid": identity.uuid,
        "fingerprint": identity.public_fingerprint(),
        "created_at": identity.created_at,
    }


@route("axioms.list")
def axioms_list(params: list) -> dict:
    from ciel.core.axioms import AXIOMS
    return {letter: {"name": a.name, "measure": a.measure}
            for letter, a in AXIOMS.items()}


@route("ethics.filter")
def ethics_filter(params: list) -> dict:
    action = params[0] if params else ""
    from ciel.ethics.filter import EthicsFilter
    ef = EthicsFilter()
    return ef.validate(action).to_dict()


@route("system.doctor")
def system_doctor(params: list) -> dict:
    checks = {
        "python_runtime": sys.version,
        "bridge_status": "connected",
        "modules_loaded": list(ROUTER.keys()),
    }
    return checks


# ── Main loop ───────────────────────────────────────────

def main():
    # Signal readiness
    print("CIEL_BRIDGE_READY", flush=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            method = request.get("method", "")
            params = request.get("params", [])
            request_id = request.get("id", 0)

            if method in ROUTER:
                try:
                    result = ROUTER[method](params)
                    response = {
                        "jsonrpc": "2.0",
                        "result": result,
                        "id": request_id,
                    }
                except Exception as e:
                    response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -1, "message": f"{type(e).__name__}: {e}"},
                        "id": request_id,
                    }
                    traceback.print_exc()
            else:
                response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": request_id,
                }
        except json.JSONDecodeError as e:
            response = {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": f"Parse error: {e}"},
                "id": 0,
            }
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
