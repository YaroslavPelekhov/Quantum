"""Point-query tensor-train completion by deterministic bidirectional ALS."""

from __future__ import annotations

import numpy as np

from contrastive_core import canonical_tt_ranks


def indices_to_bits(indices: np.ndarray, sites: int) -> np.ndarray:
    indices = np.asarray(indices, dtype=np.int64)
    shifts = np.arange(sites - 1, -1, -1, dtype=np.int64)
    return ((indices[:, None] >> shifts[None, :]) & 1).astype(np.uint8)


def tt_parameter_count_from_ranks(ranks: list[int]) -> int:
    return int(sum(ranks[i] * 2 * ranks[i + 1] for i in range(len(ranks) - 1)))


def random_cores(sites: int, max_rank: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    ranks = canonical_tt_ranks(sites, 2, max_rank)
    cores = [
        rng.standard_normal((ranks[i], 2, ranks[i + 1]))
        / np.sqrt(max(1, 2 * ranks[i]))
        for i in range(sites)
    ]
    for site in range(sites - 1):
        shape = cores[site].shape
        matrix = cores[site].reshape(shape[0] * 2, shape[2])
        q, r = np.linalg.qr(matrix, mode="reduced")
        cores[site] = q.reshape(shape[0], 2, shape[2])
        cores[site + 1] = np.tensordot(r, cores[site + 1], axes=(1, 0))
    return cores


def predict_bits(cores: list[np.ndarray], bits: np.ndarray) -> np.ndarray:
    values = np.ones((bits.shape[0], 1), dtype=np.float64)
    for site, core in enumerate(cores):
        selected = np.transpose(core[:, bits[:, site], :], (1, 0, 2))
        values = np.einsum("na,nab->nb", values, selected, optimize=True)
    return values[:, 0]


def predict_indices(
    cores: list[np.ndarray], indices: np.ndarray, sites: int
) -> np.ndarray:
    return predict_bits(cores, indices_to_bits(indices, sites))


def left_environments(cores: list[np.ndarray], bits: np.ndarray) -> list[np.ndarray]:
    environments = [np.ones((bits.shape[0], 1), dtype=np.float64)]
    for site, core in enumerate(cores):
        selected = np.transpose(core[:, bits[:, site], :], (1, 0, 2))
        environments.append(
            np.einsum("na,nab->nb", environments[-1], selected, optimize=True)
        )
    return environments


def right_environments(cores: list[np.ndarray], bits: np.ndarray) -> list[np.ndarray]:
    sites = len(cores)
    environments: list[np.ndarray | None] = [None] * (sites + 1)
    environments[sites] = np.ones((bits.shape[0], 1), dtype=np.float64)
    for site in range(sites - 1, -1, -1):
        core = cores[site]
        selected = np.transpose(core[:, bits[:, site], :], (1, 0, 2))
        environments[site] = np.einsum(
            "nab,nb->na", selected, environments[site + 1], optimize=True
        )
    return environments  # type: ignore[return-value]


def solve_local_core(
    left: np.ndarray,
    right: np.ndarray,
    bit: np.ndarray,
    targets: np.ndarray,
    relative_ridge: float,
) -> np.ndarray:
    left_rank, right_rank = left.shape[1], right.shape[1]
    core = np.zeros((left_rank, 2, right_rank), dtype=np.float64)
    for value in (0, 1):
        selected = bit == value
        features = np.einsum(
            "na,nb->nab", left[selected], right[selected], optimize=True
        ).reshape(int(selected.sum()), left_rank * right_rank)
        gram = features.T @ features
        rhs = features.T @ targets[selected]
        scale = float(np.trace(gram) / max(1, gram.shape[0]))
        ridge = relative_ridge * max(scale, np.finfo(float).tiny)
        gram.flat[:: gram.shape[0] + 1] += ridge
        try:
            solution = np.linalg.solve(gram, rhs)
        except np.linalg.LinAlgError:
            solution = np.linalg.lstsq(gram, rhs, rcond=1e-12)[0]
        core[:, value, :] = solution.reshape(left_rank, right_rank)
    return core


def fit_tt_als(
    indices: np.ndarray,
    targets: np.ndarray,
    sites: int,
    max_rank: int,
    sweeps: int,
    relative_ridge: float,
    seed: int,
) -> tuple[list[np.ndarray], dict]:
    bits = indices_to_bits(indices, sites)
    targets = np.asarray(targets, dtype=np.float64)
    cores = random_cores(sites, max_rank, seed)
    initial = predict_bits(cores, bits)
    initial_scale = float(np.std(targets) / max(np.std(initial), np.finfo(float).tiny))
    cores[-1] *= initial_scale
    history = []

    for sweep in range(sweeps):
        right = right_environments(cores, bits)
        left = np.ones((bits.shape[0], 1), dtype=np.float64)
        for site in range(sites):
            core = solve_local_core(
                left, right[site + 1], bits[:, site], targets, relative_ridge
            )
            if site < sites - 1:
                shape = core.shape
                q, r = np.linalg.qr(
                    core.reshape(shape[0] * 2, shape[2]), mode="reduced"
                )
                core = q.reshape(shape)
                cores[site + 1] = np.tensordot(r, cores[site + 1], axes=(1, 0))
            cores[site] = core
            selected = np.transpose(core[:, bits[:, site], :], (1, 0, 2))
            left = np.einsum("na,nab->nb", left, selected, optimize=True)

        lefts = left_environments(cores, bits)
        right_current = np.ones((bits.shape[0], 1), dtype=np.float64)
        for site in range(sites - 1, -1, -1):
            core = solve_local_core(
                lefts[site], right_current, bits[:, site], targets, relative_ridge
            )
            if site > 0:
                shape = core.shape
                matrix = core.reshape(shape[0], 2 * shape[2])
                q, r = np.linalg.qr(matrix.T, mode="reduced")
                core = q.T.reshape(shape)
                cores[site - 1] = np.tensordot(
                    cores[site - 1], r.T, axes=(2, 0)
                )
            cores[site] = core
            selected = np.transpose(core[:, bits[:, site], :], (1, 0, 2))
            right_current = np.einsum(
                "nab,nb->na", selected, right_current, optimize=True
            )

        prediction = predict_bits(cores, bits)
        residual = prediction - targets
        rmse = float(np.sqrt(np.mean(np.square(residual))))
        relative = rmse / max(float(np.sqrt(np.mean(np.square(targets)))), np.finfo(float).tiny)
        history.append({
            "sweep": sweep + 1,
            "training_rmse": rmse,
            "training_relative_rmse": relative,
        })
    ranks = [cores[0].shape[0]] + [core.shape[2] for core in cores]
    return cores, {
        "max_rank": max(ranks),
        "ranks": ranks,
        "parameter_count": tt_parameter_count_from_ranks(ranks),
        "history": history,
    }


def sample_distinct_indices(
    total: int,
    count: int,
    excluded: set[int],
    seed: int,
) -> np.ndarray:
    if count + len(excluded) >= total:
        raise ValueError("Requested sample is not sparse")
    rng = np.random.default_rng(seed)
    selected: set[int] = set()
    ordered: list[int] = []
    while len(selected) < count:
        needed = count - len(selected)
        candidates = rng.integers(0, total, size=max(1024, 2 * needed), dtype=np.int64)
        for raw in candidates:
            value = int(raw)
            if value in excluded or value in selected:
                continue
            selected.add(value)
            ordered.append(value)
            if len(ordered) == count:
                break
    return np.asarray(ordered, dtype=np.int64)
