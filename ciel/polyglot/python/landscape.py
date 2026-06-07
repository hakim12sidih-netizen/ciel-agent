"""
Hydra Polyglot — Python numerical compute
Standalone numpy-based "fitness landscape" explorer. The TypeScript layer
can spawn this script via subprocess to perform matrix math without a Rust
toolchain (numpy is already installed in the test env).

Run:  python3 polyglot/python/landscape.py --dim 4 --steps 200
"""

import argparse
import json
import sys
import numpy as np


def run(dim: int, steps: int, seed: int) -> dict:
    """Run a simple policy gradient on a synthetic fitness landscape.

    Returns JSON-serializable stats.
    """
    rng = np.random.default_rng(seed)
    weights = rng.normal(0, 0.1, size=dim)
    lr = 0.01
    rewards = []

    for step in range(steps):
        # Synthetic fitness: dot product with a hidden target
        target = np.array([1.0 / (i + 1) for i in range(dim)])
        logits = weights @ target
        reward = float(logits)
        rewards.append(reward)
        # Gradient: reward * weight
        grad = reward * weights
        weights = weights + lr * grad / (1 + abs(reward))

    return {
        "dim": dim,
        "steps": steps,
        "final_reward": rewards[-1],
        "max_reward": max(rewards),
        "min_reward": min(rewards),
        "mean_reward": float(np.mean(rewards)),
        "std_reward": float(np.std(rewards)),
        "weights_norm": float(np.linalg.norm(weights)),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dim", type=int, default=4)
    p.add_argument("--steps", type=int, default=100)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    result = run(args.dim, args.steps, args.seed)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
