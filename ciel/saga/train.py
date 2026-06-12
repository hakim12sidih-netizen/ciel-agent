"""Orchestrateur d'entraînement pour CIEL SAGA 1."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import torch

from ciel.saga.config import SagaConfig
from ciel.saga.model import SagaModel
from ciel.saga.tokenizer import SagaTokenizer
from ciel.saga.data import TextFileDataset, DataLoader
from ciel.saga.phases import PHASE_REGISTRY
import ciel.saga.phase_impls  # noqa: F401 — enregistre les phases


def create_deepspeed_config(config: SagaConfig) -> dict:
    return {
        "train_batch_size": 1,
        "gradient_accumulation_steps": 1,
        "optimizer": {
            "type": "AdamW",
            "params": {
                "lr": 3e-4,
                "betas": [0.9, 0.95],
                "eps": 1e-8,
                "weight_decay": 0.1,
            },
        },
        "scheduler": {
            "type": "WarmupCosine",
            "params": {
                "warmup_min_lr": 0,
                "warmup_max_lr": 3e-4,
                "warmup_num_steps": 2000,
                "total_num_steps": 100000,
            },
        },
        "fp16": {
            "enabled": False,
        },
        "bf16": {
            "enabled": True if config.training.mixed_precision == "bf16" else False,
        },
        "zero_optimization": {
            "stage": config.training.zero_stage,
            "offload_optimizer": {
                "device": "cpu" if config.training.offload else "none",
            },
            "contiguous_gradients": True,
            "overlap_comm": True,
        },
        "gradient_clipping": 1.0,
        "steps_per_print": 10,
        "wall_clock_breakdown": False,
    }


def main():
    parser = argparse.ArgumentParser(description="CIEL SAGA 1 — Entraînement 10B MoE")
    parser.add_argument("--data", type=str, required=True, help="Chemin vers les données d'entraînement")
    parser.add_argument("--output", type=str, default=str(Path.home() / ".ciel" / "saga1"), help="Répertoire de sortie")
    parser.add_argument("--phase", type=str, default="all", help="Phase spécifique ou 'all'")
    parser.add_argument("--resume", type=str, default=None, help="Checkpoint à reprendre")
    parser.add_argument("--compile", action="store_true", default=True, help="Compiler le modèle")
    parser.add_argument("--no-compile", action="store_false", dest="compile")
    parser.add_argument("--epochs", type=int, default=None, help="Surcharger le nombre d'epochs")
    parser.add_argument("--batch-size", type=int, default=None, help="Surcharger la taille de batch")
    parser.add_argument("--lr", type=float, default=None, help="Surcharger le learning rate")
    parser.add_argument("--deepspeed", action="store_true", help="Activer DeepSpeed")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA non disponible, fallback CPU")
        args.device = "cpu"

    config = SagaConfig()
    config.training.output_dir = args.output
    config.device = args.device

    if args.deepspeed:
        ds_config = create_deepspeed_config(config)
        ds_path = Path(args.output) / "ds_config.json"
        ds_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ds_path, "w") as f:
            json.dump(ds_config, f, indent=2)
        config.training.deepspeed_config = str(ds_path)

    os.makedirs(args.output, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  CIEL SAGA 1 — Lancement de l'entraînement")
    print(f"  Device: {args.device} | {'DeepSpeed' if args.deepspeed else 'PyTorch natif'}")
    print(f"  Données: {args.data}")
    print(f"  Output: {args.output}")
    print(f"{'='*60}\n")

    tokenizer = SagaTokenizer()
    model = SagaModel(config.model)
    model = model.to(config.device)

    params = model.get_param_count()
    memory = model.get_memory_estimate()
    print(f"  Paramètres: {params['total_b']:.2f}B")
    print(f"  Estimation mémoire (bf16): {memory['total_bf16_estimate_gb']} GB")
    print(f"\n{'-'*60}\n")

    data_path = Path(args.data)
    paths = [str(p) for p in data_path.glob("*.txt")] + [str(p) for p in data_path.glob("*.jsonl")]
    if data_path.is_file():
        paths = [str(data_path)]

    if not paths:
        print(f"Aucune donnée trouvée dans {args.data}")
        print(f"Création de données synthétiques pour test...")
        sample = Path(args.output) / "sample_data.txt"
        with open(sample, "w") as f:
            for i in range(100):
                f.write(f"CIEL SAGA 1 — Exemple de texte d'entraînement numéro {i}. " * 20 + "\n")
        paths = [str(sample)]

    dataset = TextFileDataset(paths, tokenizer, max_length=2048)
    loader = DataLoader(dataset, batch_size=args.batch_size or config.training.phases[0].batch_size, shuffle=True, pin_memory=True)

    phases_to_run = list(PHASE_REGISTRY.items())
    if args.phase != "all":
        phases_to_run = [(k, v) for k, v in phases_to_run if k == args.phase]

    for phase_name, phase_fn in phases_to_run:
        if args.epochs:
            for p in config.training.phases:
                if p.name == phase_name:
                    p.epochs = args.epochs
        if args.lr:
            for p in config.training.phases:
                if p.name == phase_name:
                    p.learning_rate = args.lr

        phase_config = next((p for p in config.training.phases if p.name == phase_name), None)
        if phase_config:
            if args.batch_size:
                loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, pin_memory=True)

        print(f"\n{'#'*60}")
        print(f"  Phase: {phase_name}")
        print(f"{'#'*60}\n")

        if args.compile and args.device == "cuda" and hasattr(torch, "compile"):
            try:
                model = torch.compile(model)
                print("  Modèle compilé (torch.compile)")
            except Exception as e:
                print(f"  Compilation impossible: {e}")

        phase_fn(model, tokenizer, loader, config)
        print(f"\n  ✓ Phase {phase_name} terminée\n")

        ckpt_path = Path(args.output) / "checkpoints"
        ckpt_path.mkdir(parents=True, exist_ok=True)
        torch.save({
            "model_state": model.state_dict(),
            "phase": phase_name,
            "config": str(config),
        }, ckpt_path / f"{phase_name}_final.pt")
        print(f"  ✓ Checkpoint sauvegardé: {ckpt_path / f'{phase_name}_final.pt'}")

    print(f"\n{'='*60}")
    print(f"  ✓ Entraînement CIEL SAGA 1 terminé !")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
