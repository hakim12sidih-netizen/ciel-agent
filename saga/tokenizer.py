"""Tokenizer BPE 65536 tokens pour CIEL SAGA 1."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import torch

TOKENIZER_FILE = "tokenizer.json"
SPECIAL_TOKENS = {
    "<unk>": 0,
    "<pad>": 1,
    "<eos>": 2,
    "<bos>": 3,
    "<reason>": 4,
    "<create>": 5,
    "<verify>": 6,
    "<remember>": 7,
    "<act>": 8,
    "<thinking>": 9,
    "<plan>": 10,
    "<tool>": 11,
    "<output>": 12,
    "<res>": 13,
    "<confidence>": 14,
    "<doubt>": 15,
    "<socratic>": 16,
    "<memory>": 17,
    "<sys>": 18,
    "<user>": 19,
    "<assistant>": 20,
    "<sep>": 21,
}


class SagaTokenizer:
    """Tokenizer BPE 65536 tokens avec tokens spéciaux pour MoE et workflow."""

    def __init__(self, vocab_path: Optional[str] = None):
        self.special_tokens = SPECIAL_TOKENS
        self.vocab_size = 65536
        self.num_special = len(SPECIAL_TOKENS)
        self.vocab: dict[str, int] = {}
        self.inv_vocab: dict[int, str] = {}
        self.merges: list[tuple[str, str]] = []

        if vocab_path and os.path.exists(vocab_path):
            self.load(vocab_path)
        else:
            self._init_vocab()

    def _init_vocab(self):
        for token, tid in self.special_tokens.items():
            self.vocab[token] = tid
            self.inv_vocab[tid] = token
        for i in range(self.num_special, self.vocab_size):
            t = f"<token_{i}>"
            self.vocab[t] = i
            self.inv_vocab[i] = t
        self._build_byte_base()

    def _build_byte_base(self):
        next_id = self.num_special
        for b in range(256):
            t = bytes([b]).decode('latin-1')
            if t not in self.vocab:
                self.vocab[t] = next_id
                self.inv_vocab[next_id] = t
                next_id += 1

    @property
    def pad_token_id(self) -> int:
        return self.special_tokens.get("<pad>", 1)

    @property
    def eos_token_id(self) -> int:
        return self.special_tokens.get("<eos>", 2)

    @property
    def bos_token_id(self) -> int:
        return self.special_tokens.get("<bos>", 3)

    def encode(self, text: str, add_special: bool = True) -> list[int]:
        tokens = [self.special_tokens["<bos>"]] if add_special else []
        chars = list(text)
        i = 0
        while i < len(chars):
            c = chars[i]
            if c in self.vocab:
                tokens.append(self.vocab[c])
            else:
                for b in c.encode('utf-8'):
                    byte_str = bytes([b]).decode('latin-1')
                    tokens.append(self.vocab.get(byte_str, self.special_tokens["<unk>"]))
            i += 1
        if add_special:
            tokens.append(self.special_tokens["<eos>"])
        return tokens

    def decode(self, token_ids: list[int], skip_special: bool = True) -> str:
        chars = []
        for tid in token_ids:
            t = self.inv_vocab.get(tid, "")
            if skip_special and tid < self.num_special:
                if tid in (self.special_tokens.get(t, -1) for t in ["<bos>", "<eos>", "<pad>", "<unk>"]):
                    continue
                chars.append(t)
            elif tid >= self.num_special:
                if t.startswith("<token_"):
                    continue
                chars.append(t)
            else:
                chars.append(t)
        return "".join(chars)

    def encode_batch(self, texts: list[str]) -> list[list[int]]:
        return [self.encode(t) for t in texts]

    def collate(self, sequences: list[list[int]], max_length: Optional[int] = None) -> torch.Tensor:
        if max_length is None:
            max_length = max(len(s) for s in sequences)
        max_length = min(max_length, 1_000_000)
        batch = torch.full((len(sequences), max_length), self.pad_token_id, dtype=torch.long)
        for i, seq in enumerate(sequences):
            length = min(len(seq), max_length)
            batch[i, :length] = torch.tensor(seq[:length], dtype=torch.long)
        return batch

    def save(self, path: str):
        data = {
            "vocab": self.vocab,
            "inv_vocab": {str(k): v for k, v in self.inv_vocab.items()},
            "merges": self.merges,
            "special_tokens": self.special_tokens,
            "vocab_size": self.vocab_size,
        }
        with open(path, "w") as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self, path: str):
        with open(path) as f:
            data = json.load(f)
        self.vocab = data["vocab"]
        self.inv_vocab = {int(k): v for k, v in data["inv_vocab"].items()}
        self.merges = data.get("merges", [])
        self.special_tokens = data.get("special_tokens", SPECIAL_TOKENS)
        self.vocab_size = data.get("vocab_size", 65536)

    def train(self, texts: list[str], vocab_size: int = 65536):
        """Entraîne le tokenizer BPE sur un corpus (placeholder pour entraînement réel)."""
        self.vocab_size = vocab_size
        self._init_vocab()

    def expert_token(self, expert_type: str) -> int:
        mapping = {
            "reason": 4, "create": 5, "verify": 6,
            "remember": 7, "act": 8,
        }
        return mapping.get(expert_type, self.special_tokens["<unk>"])
