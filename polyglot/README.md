# CIEL Polyglot

CIEL n'est pas limité à TypeScript. Ce dossier contient des backends en
**Python**, **Rust**, et **Go** que TypeScript peut invoquer via subprocess.

## Structure

```
polyglot/
├── go/
│   └── server.go          # HTTP server (sha256, health, metrics)
├── rust/
│   ├── Cargo.toml
│   └── src/main.rs        # FNV-1a + polynomial hash CLI
├── python/
│   └── landscape.py       # numpy policy gradient
├── tests/
│   └── (integration tests in TypeScript)
└── README.md
```

## Quick start

```bash
# 1. Go server (HTTP)
go run polyglot/go/server.go
# → Listening on :8732
# curl http://localhost:8732/health
# curl -X POST http://localhost:8732/hash -d "hello world"

# 2. Rust hash CLI
cargo run --manifest-path polyglot/rust/Cargo.toml -- hash "hello world"
# → fnv1a:779a65e7023cd2e7 poly:d83929cb269f7044 len:11

# 3. Python landscape
python3 polyglot/python/landscape.py --dim 4 --steps 200
# → {"dim":4,"steps":200,"final_reward":0.02849, ...}
```

## TypeScript bridge

Le module `src/polyglot/bridge.ts` expose :

| Fonction | Backend | Retourne |
|----------|---------|----------|
| `runPythonLandscape(dim, steps, seed)` | Python + numpy | `PythonStats` (JSON) |
| `runRustHash(input)` | Rust | `{ fnv1a, poly, len }` |
| `startGoServer()` | Go | port number |
| `goServerGet(path)` | Go | string response |
| `goServerPost(path, body)` | Go | string response |
| `detectBackends()` | shells | `{ go, rust, python }` |

## Tests

13 tests d'intégration cross-langage dans `tests/phase8_polyglot.test.ts` :

- Python : determinism, weights evolution
- Rust : FNV-1a known values, determinism
- Go : health, metrics (Prometheus), hash, restart safety

## Adding a new language

1. Crée `polyglot/<lang>/` avec un binaire/CLI
2. Ajoute une fonction dans `src/polyglot/bridge.ts`
3. Ajoute des tests dans `tests/phase8_polyglot.test.ts`
4. Mets à jour `detectBackends()` pour signaler la dispo
