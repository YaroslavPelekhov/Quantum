from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from qaoa_mis import ExactSpace, GraphInstance, distribution_metrics


@dataclass
class FeasibleMixerSimulator:
    graph: GraphInstance
    exact: ExactSpace

    def __post_init__(self) -> None:
        self._size = 1 << self.graph.n
        masks = self.exact.masks
        neighbors = [0] * self.graph.n
        for u, v in self.graph.edges:
            neighbors[u] |= 1 << v
            neighbors[v] |= 1 << u
        self._pairs = []
        for vertex in range(self.graph.n):
            base = masks[((masks & (1 << vertex)) == 0) & ((masks & neighbors[vertex]) == 0)]
            self._pairs.append((base.astype(np.int64), (base | (1 << vertex)).astype(np.int64)))
        self._orders = {
            0: np.arange(self.graph.n, dtype=int),
            1: np.argsort(self.graph.degrees, kind="stable"),
            2: np.argsort(-self.graph.degrees, kind="stable"),
            3: np.random.default_rng(8675309 + self.graph.n + len(self.graph.edges)).permutation(self.graph.n),
        }

    def probabilities(self, params: np.ndarray) -> np.ndarray:
        """Three feasible mixer sweeps and two nontrivial cost phases.

        Genome: [order_policy, beta_1, beta_2, beta_3, gamma_2, gamma_3].
        The first cost phase is omitted because |0...0> is its eigenstate.
        """
        params = np.asarray(params, dtype=float)
        if len(params) != 6:
            raise ValueError("Feasible mixer expects six parameters")
        order_policy = min(3, max(0, int(np.floor(params[0]))))
        betas = params[1:4]
        gammas = params[4:6]
        state = np.zeros(self._size, dtype=np.complex128)
        state[0] = 1.0
        for layer, beta in enumerate(betas):
            cosine = np.cos(float(beta))
            sine = -1j * np.sin(float(beta))
            for vertex in self._orders[order_policy]:
                zero, one = self._pairs[int(vertex)]
                amplitude_zero = state[zero].copy()
                amplitude_one = state[one].copy()
                state[zero] = cosine * amplitude_zero + sine * amplitude_one
                state[one] = sine * amplitude_zero + cosine * amplitude_one
            if layer < 2:
                # MIS cost is -|S|. exp(-i*gamma*C) = exp(+i*gamma*|S|).
                state *= np.exp(1j * float(gammas[layer]) * self.exact.sizes)
        probabilities = np.abs(state) ** 2
        probabilities /= probabilities.sum()
        return probabilities

    def metrics(self, params: np.ndarray) -> dict[str, float]:
        return distribution_metrics(self.probabilities(params), self.exact)
