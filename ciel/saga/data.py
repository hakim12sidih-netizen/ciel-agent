"""Pipeline de données pour les phases d'entraînement CIEL SAGA 1."""
from __future__ import annotations

import json
import math
import os
import random
from pathlib import Path
from typing import Optional, Iterator

import torch
from torch.utils.data import Dataset, IterableDataset, DataLoader

from ciel.saga.tokenizer import SagaTokenizer


class TextFileDataset(Dataset):
    """Dataset sur fichiers texte avec streaming mémoire."""
    def __init__(self, paths: list[str], tokenizer: SagaTokenizer,
                 max_length: int = 8192, overlap: int = 512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.overlap = overlap
        self.chunks: list[list[int]] = []

        for path in paths:
            with open(path) as f:
                text = f.read()
            tokens = tokenizer.encode(text, add_special=False)
            step = max_length - overlap
            for i in range(0, len(tokens), step):
                chunk = tokens[i:i + max_length]
                if len(chunk) >= 128:
                    self.chunks.append(chunk)

    def __len__(self) -> int:
        return len(self.chunks)

    def __getitem__(self, idx: int) -> dict:
        tokens = self.chunks[idx]
        input_ids = torch.tensor(tokens, dtype=torch.long)
        labels = input_ids.clone()
        return {"input_ids": input_ids, "labels": labels}


class LongContextDataset(IterableDataset):
    """Dataset streaming pour contexte long (1M tokens)."""
    def __init__(self, data_dir: str, tokenizer: SagaTokenizer,
                 seq_length: int = 1_000_000, epoch_size: int = 1000):
        self.data_dir = Path(data_dir)
        self.tokenizer = tokenizer
        self.seq_length = seq_length
        self.epoch_size = epoch_size
        self.files = list(self.data_dir.glob("*.txt")) + list(self.data_dir.glob("*.jsonl"))

    def __iter__(self) -> Iterator[dict]:
        for _ in range(self.epoch_size):
            if self.files:
                path = random.choice(self.files)
                try:
                    with open(path) as f:
                        if path.suffix == ".jsonl":
                            line = random.choice(f.readlines())
                            data = json.loads(line)
                            text = data.get("text", "")
                        else:
                            text = f.read()
                    tokens = self.tokenizer.encode(text, add_special=True)
                    if len(tokens) > self.seq_length:
                        start = random.randint(0, len(tokens) - self.seq_length)
                        tokens = tokens[start:start + self.seq_length]
                    input_ids = torch.tensor(tokens, dtype=torch.long)
                    labels = input_ids.clone()
                    yield {"input_ids": input_ids, "labels": labels}
                except Exception:
                    continue


class MoEBatchProcessor:
    """Prépare les batches avec routing expert pour l'entraînement MoE."""
    def __init__(self, tokenizer: SagaTokenizer):
        self.tokenizer = tokenizer

    def prepare_expert_batch(self, batch: dict) -> dict:
        expert_types = ["reason", "create", "verify", "remember", "act"]
        seq_len = batch["input_ids"].shape[1]
        expert_token_ids = torch.full((len(expert_types), seq_len), fill_value=0)
        for i, etype in enumerate(expert_types):
            token_id = self.tokenizer.expert_token(etype)
            expert_token_ids[i] = token_id
        return {
            **batch,
            "expert_types": expert_types,
            "expert_token_ids": expert_token_ids,
        }


def create_dataloader(
    data_config: dict,
    tokenizer: SagaTokenizer,
    batch_size: int = 4,
    seq_length: int = 8192,
    shuffle: bool = True,
    num_workers: int = 2,
) -> DataLoader:
    """Crée un DataLoader à partir de la configuration."""
    paths = data_config.get("paths", [])
    dataset = TextFileDataset(paths, tokenizer, max_length=seq_length)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True,
    )
