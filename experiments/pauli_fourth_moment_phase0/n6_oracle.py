"""GPU separation oracle over all six-qubit stabilizer states."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import torch
from scipy.sparse import csc_matrix


class N6Oracle:
    qubits = 6
    dimension = 64
    paulis = 4096

    def __init__(self, context_path: Path, device: str = "cuda") -> None:
        self.contexts = np.load(context_path, mmap_mode="r")
        if self.contexts.shape != (4_922_775, 6):
            raise ValueError(self.contexts.shape)
        self.device = torch.device(device)
        self.popcount = torch.tensor(
            [value.bit_count() for value in range(self.dimension)],
            dtype=torch.int64,
            device=self.device,
        )
        self.quadratic = torch.tensor(
            [
                ((label & 63) & (label >> 6)).bit_count()
                for label in range(self.paulis)
            ],
            dtype=torch.int64,
            device=self.device,
        )

    def expand_contexts(self, bases: torch.Tensor):
        count = bases.shape[0]
        labels = torch.zeros((count, 1), dtype=torch.int64, device=self.device)
        signs = torch.ones((count, 1), dtype=torch.float32, device=self.device)
        for generator in range(self.qubits):
            label = bases[:, generator : generator + 1]
            combined = labels ^ label
            exponent = (
                self.quadratic[labels]
                + self.quadratic[label]
                - self.quadratic[combined]
                + 2 * self.popcount[(labels >> 6) & (label & 63)]
            ) & 3
            if torch.any(exponent & 1):
                raise ValueError("noncommuting context")
            multiplier = 1.0 - 2.0 * ((exponent >> 1) & 1).to(torch.float32)
            labels = torch.cat((labels, combined), dim=1)
            signs = torch.cat((signs, signs * multiplier), dim=1)
        return labels, signs

    @staticmethod
    def _fwht(values: torch.Tensor) -> torch.Tensor:
        width = 1
        while width < 64:
            view = values.view(-1, 64 // (2 * width), 2, width)
            left = view[:, :, 0, :].clone()
            right = view[:, :, 1, :].clone()
            view[:, :, 0, :] = left + right
            view[:, :, 1, :] = left - right
            width *= 2
        return values

    def separate(self, witness, batch=240_000, topk=64, verbose=False):
        witness = np.asarray(witness, dtype=np.float32)
        if witness.shape != (4095,):
            raise ValueError(witness.shape)
        padded = torch.zeros(4096, dtype=torch.float32, device=self.device)
        padded[1:] = torch.from_numpy(witness).to(self.device)
        best = []
        started = time.time()
        for low in range(0, len(self.contexts), batch):
            high = min(low + batch, len(self.contexts))
            bases = torch.from_numpy(
                np.asarray(self.contexts[low:high], dtype=np.int64)
            ).to(self.device)
            labels, signs = self.expand_contexts(bases)
            scores = self._fwht(padded[labels] * signs).flatten()
            count = min(topk, scores.numel())
            values, indices = torch.topk(scores, count)
            best.extend(
                (float(value), low + int(index) // 64, int(index) % 64)
                for value, index in zip(values.cpu().numpy(), indices.cpu().numpy())
            )
            best = sorted(best, reverse=True)[:topk]
            if verbose and high == len(self.contexts):
                print(f"support={best[0][0]} seconds={time.time() - started:.3f}")
        return best

    def column(self, context: int, eigenmask: int) -> np.ndarray:
        bases = torch.from_numpy(
            np.asarray(self.contexts[context : context + 1], dtype=np.int64)
        ).to(self.device)
        labels, signs = self.expand_contexts(bases)
        labels = labels[0].cpu().numpy()
        signs = signs[0].cpu().numpy()
        output = np.zeros(4095, dtype=np.float32)
        for subset in range(1, 64):
            eigenvalue = -1 if (subset & eigenmask).bit_count() & 1 else 1
            output[labels[subset] - 1] = signs[subset] * eigenvalue
        return output

    def incidence(self, context_indices) -> csc_matrix:
        indices = np.asarray(context_indices, dtype=np.int64)
        bases = torch.from_numpy(
            np.asarray(self.contexts[indices], dtype=np.int64)
        ).to(self.device)
        labels, _ = self.expand_contexts(bases)
        rows = labels[:, 1:].cpu().numpy().reshape(-1) - 1
        columns = np.repeat(np.arange(len(indices)), 63)
        return csc_matrix(
            (np.ones(len(rows)), (rows, columns)), shape=(4095, len(indices))
        )
