"""Benchmark-grade evolutionary QAOA transfer on full QOBLIB MIS instances."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import networkx as nx
import numpy as np
from qiskit_aer import AerSimulator


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASELINE_REPO = ROOT / "baselines" / "qoblib-solutions"
BASELINE_DIR = (
    BASELINE_REPO
    / "experiments/quantum/ibm_simulator/07-independentset/es60fst02"
    / "20260611_qaoa_mis_mps_simulation"
)
QOBLIB = ROOT / "QOBLIB"
RESULTS = HERE / "results"
sys.path.insert(0, str(BASELINE_DIR))

from utils import (  # noqa: E402
    MISPostprocessor,
    mis_hamiltonian,
    parse_gph_file,
    qaoa_mis,
    reduce_graph_for_quantum,
)


P = 15
LAMBDA = 1.5
MAX_DEGREE = 4
BOUNDS = np.array([[0.15, 1.20], [0.05, 1.00], [0.30, 2.50], [0.30, 2.50]])
BASELINE = np.array([0.7, 0.4, 1.0, 1.0])
BKS = {"es60fst01": 60, "es60fst02": 88, "es60fst03": 55, "es60fst04": 78}
TRAIN_NAMES = ("es60fst01", "es60fst03")
VALIDATION_NAME = "es60fst04"
TEST_NAME = "es60fst02"


@dataclass
class PreparedCase:
    name: str
    bks: int
    graph: nx.Graph
    reduction: object
    decoder: MISPostprocessor
    circuit: object
    original_vertices: int
    original_edges: int
    reduced_vertices: int
    reduced_edges: int


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def jsonable(value):
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(payload), indent=2) + "\n", encoding="utf-8")


def git_commit(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def provenance() -> dict:
    import qiskit
    import qiskit_aer

    return {
        "created_at": utc_now(),
        "python": sys.version,
        "platform": platform.platform(),
        "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__,
        "numpy": np.__version__,
        "qoblib_solutions_commit": git_commit(BASELINE_REPO),
        "qoblib_path": str(QOBLIB),
        "protocol_sha256": hashlib.sha256(
            (HERE / "FROZEN_PROTOCOL.md").read_bytes()
        ).hexdigest(),
    }


def schedule(genome: np.ndarray, p: int = P) -> tuple[np.ndarray, np.ndarray]:
    delta_beta, delta_gamma, beta_power, gamma_power = map(float, genome)
    k = np.arange(1, p + 1, dtype=float)
    betas = delta_beta * ((p - k + 1.0) / p) ** beta_power
    gammas = delta_gamma * (k / p) ** gamma_power
    return betas, gammas


def prepare_case(name: str) -> PreparedCase:
    graph = parse_gph_file(QOBLIB / "07-independentset/instances" / f"{name}.gph")
    reduction = reduce_graph_for_quantum(graph, max_degree=MAX_DEGREE)
    reduced = reduction.reduced_graph
    if not reduced.number_of_nodes():
        raise RuntimeError(f"{name}: reduction produced an empty quantum kernel")
    mapping = {node: i for i, node in enumerate(sorted(reduced.nodes()))}
    reduced_zero = nx.relabel_nodes(reduced, mapping)
    hamiltonian = mis_hamiltonian(reduced_zero, lambd=LAMBDA)
    circuit = qaoa_mis(
        np.array([0.0] * P), np.array([0.0] * P), hamiltonian, reduced.number_of_nodes()
    )
    decoder = MISPostprocessor(graph, reduction, repair_samples=False)
    return PreparedCase(
        name=name,
        bks=BKS[name],
        graph=graph,
        reduction=reduction,
        decoder=decoder,
        circuit=circuit,
        original_vertices=graph.number_of_nodes(),
        original_edges=graph.number_of_edges(),
        reduced_vertices=reduced.number_of_nodes(),
        reduced_edges=reduced.number_of_edges(),
    )


def bind_case(case: PreparedCase, genome: np.ndarray):
    """Rebuild a numeric circuit; small overhead avoids parameter-order ambiguity."""
    reduced = case.reduction.reduced_graph
    mapping = {node: i for i, node in enumerate(sorted(reduced.nodes()))}
    hamiltonian = mis_hamiltonian(nx.relabel_nodes(reduced, mapping), lambd=LAMBDA)
    betas, gammas = schedule(genome)
    return qaoa_mis(gammas, betas, hamiltonian, case.reduced_vertices)


def wilson_lower(successes: int, total: int, z: float = 1.96) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    den = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    radius = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total))
    return (centre - radius) / den


def summarize_counts(case: PreparedCase, counts: dict[str, int]) -> dict:
    total = int(sum(counts.values()))
    feasible = bks_hits = near_hits = 0
    weighted_quality = 0.0
    weighted_selected = 0
    best = None
    distribution: dict[int, int] = {}
    for bitstring, count_value in counts.items():
        count = int(count_value)
        decoded = case.decoder.decode(bitstring)
        if not decoded.raw_feasible:
            continue
        size = int(decoded.raw_selected)
        feasible += count
        weighted_selected += count * size
        weighted_quality += count * min(size / case.bks, 1.0)
        bks_hits += count if size >= case.bks else 0
        near_hits += count if size >= case.bks - 1 else 0
        best = size if best is None else max(best, size)
        distribution[size] = distribution.get(size, 0) + count
    metrics = {
        "total_shots": total,
        "feasible_shots": feasible,
        "feasible_rate": feasible / total if total else 0.0,
        "bks_hits": bks_hits,
        "bks_rate": bks_hits / total if total else 0.0,
        "near_bks_hits": near_hits,
        "near_bks_rate": near_hits / total if total else 0.0,
        "quality_mass": weighted_quality / total if total else 0.0,
        "conditional_mean_size": weighted_selected / feasible if feasible else None,
        "best_size": best,
        "approximation_ratio_best": None if best is None else best / case.bks,
        "distribution": dict(sorted(distribution.items())),
        "wilson_feasible": wilson_lower(feasible, total),
        "wilson_bks": wilson_lower(bks_hits, total),
        "wilson_near_bks": wilson_lower(near_hits, total),
    }
    metrics["robust_score"] = (
        2.0 * metrics["wilson_bks"]
        + metrics["wilson_near_bks"]
        + 0.5 * metrics["wilson_feasible"]
        + 0.5 * metrics["quality_mass"]
    )
    return metrics


def simulator(mode: str) -> AerSimulator:
    if mode == "mps":
        return AerSimulator(
            method="matrix_product_state",
            matrix_product_state_max_bond_dimension=64,
            matrix_product_state_truncation_threshold=1e-3,
            max_parallel_experiments=1,
        )
    return AerSimulator(method="statevector", max_parallel_experiments=1)


def evaluate_population(
    cases: list[PreparedCase],
    genomes: np.ndarray,
    shots: int,
    seed: int,
    mode: str,
) -> list[dict]:
    backend = simulator(mode)
    circuits = []
    index = []
    for gi, genome in enumerate(genomes):
        for ci, case in enumerate(cases):
            circuits.append(bind_case(case, genome))
            index.append((gi, ci))
    start = perf_counter()
    # Match the published QOBLIB/Aer-MPS submission exactly: its simulator is
    # given native RZ/RZZ/RX circuits without a hardware-basis transpilation.
    # This matters at finite MPS bond dimension because decomposing RZZ into
    # CX-RZ-CX changes the sequence at which truncation is applied.
    result = backend.run(circuits, shots=shots, seed_simulator=seed).result()
    elapsed = perf_counter() - start
    rows = [
        {"genome": genomes[i].tolist(), "instances": {}, "elapsed_batch_seconds": elapsed}
        for i in range(len(genomes))
    ]
    for result_i, (gi, ci) in enumerate(index):
        rows[gi]["instances"][cases[ci].name] = summarize_counts(
            cases[ci], result.get_counts(result_i)
        )
    for row in rows:
        scores = [m["robust_score"] for m in row["instances"].values()]
        row["score"] = float(np.mean(scores))
        row["worst_instance_score"] = float(np.min(scores))
        row["selection_score"] = 0.75 * row["score"] + 0.25 * row["worst_instance_score"]
    return rows


def random_genomes(rng: np.random.Generator, count: int) -> np.ndarray:
    return rng.uniform(BOUNDS[:, 0], BOUNDS[:, 1], size=(count, 4))


def evolutionary_search(
    cases: list[PreparedCase], population: int, generations: int, shots: int, seed: int
) -> dict:
    rng = np.random.default_rng(seed)
    genomes = random_genomes(rng, population)
    genomes[0] = BASELINE
    history = []
    for generation in range(generations):
        rows = evaluate_population(cases, genomes, shots, seed + generation * 1009, "statevector")
        for row in rows:
            row["generation"] = generation
        history.extend(rows)
        order = np.argsort([-row["selection_score"] for row in rows])
        elite_count = max(4, population // 4)
        elites = genomes[order[:elite_count]].copy()
        if generation + 1 == generations:
            break
        children = [elites[i].copy() for i in range(min(2, len(elites)))]
        scale = (BOUNDS[:, 1] - BOUNDS[:, 0]) * (0.18 * (0.72**generation))
        while len(children) < population:
            a, b = rng.choice(elite_count, size=2, replace=True)
            alpha = rng.uniform(-0.15, 1.15, size=4)
            child = alpha * elites[a] + (1.0 - alpha) * elites[b]
            child += rng.normal(0.0, scale)
            children.append(np.clip(child, BOUNDS[:, 0], BOUNDS[:, 1]))
        genomes = np.asarray(children[:population])
    best = max(history, key=lambda row: row["selection_score"])
    return {
        "method": "evolutionary_search",
        "seed": seed,
        "circuit_evaluations": population * generations * len(cases),
        "candidate_evaluations": population * generations,
        "best": best,
        "history": history,
    }


def matched_random_search(
    cases: list[PreparedCase], budget: int, shots: int, seed: int, batch: int = 24
) -> dict:
    rng = np.random.default_rng(seed)
    history = []
    for start in range(0, budget, batch):
        count = min(batch, budget - start)
        genomes = random_genomes(rng, count)
        if start == 0:
            genomes[0] = BASELINE
        rows = evaluate_population(cases, genomes, shots, seed + start * 37, "statevector")
        for row in rows:
            row["batch_start"] = start
        history.extend(rows)
    best = max(history, key=lambda row: row["selection_score"])
    return {
        "method": "matched_random_search",
        "seed": seed,
        "circuit_evaluations": budget * len(cases),
        "candidate_evaluations": budget,
        "best": best,
        "history": history,
    }


def case_metadata(case: PreparedCase) -> dict:
    summary = case.reduction.summary(case.graph)
    return {"name": case.name, "bks": case.bks, **summary}


def train(args) -> dict:
    cases = [prepare_case(name) for name in TRAIN_NAMES]
    payload = {
        "stage": "train",
        "provenance": provenance(),
        "config": vars(args),
        "cases": [case_metadata(case) for case in cases],
        "evolutionary": [],
        "random": [],
    }
    for replicate in range(args.replicates):
        seed = args.seed + replicate * 100_003
        print(f"TRAIN replicate {replicate + 1}/{args.replicates}: evolutionary", flush=True)
        payload["evolutionary"].append(
            evolutionary_search(cases, args.population, args.generations, args.train_shots, seed)
        )
        print(f"TRAIN replicate {replicate + 1}/{args.replicates}: matched random", flush=True)
        payload["random"].append(
            matched_random_search(
                cases, args.population * args.generations, args.train_shots, seed + 50_000
            )
        )
        write_json(RESULTS / "train.json", payload)
    return payload


def candidate_rows(train_payload: dict) -> list[dict]:
    rows = [{"method": "published_lr", "replicate": 0, "genome": BASELINE.tolist()}]
    for method_key in ("evolutionary", "random"):
        for replicate, result in enumerate(train_payload[method_key]):
            rows.append(
                {
                    "method": result["method"],
                    "replicate": replicate,
                    "genome": result["best"]["genome"],
                    "training_selection_score": result["best"]["selection_score"],
                }
            )
    return rows


def validate(args, train_payload: dict | None = None) -> dict:
    if train_payload is None:
        train_payload = json.loads((RESULTS / "train.json").read_text(encoding="utf-8"))
    case = prepare_case(VALIDATION_NAME)
    candidates = candidate_rows(train_payload)
    genomes = np.asarray([row["genome"] for row in candidates], dtype=float)
    print(f"VALIDATE {len(candidates)} candidates on {VALIDATION_NAME}/{case.reduced_vertices}q MPS", flush=True)
    evaluated = evaluate_population([case], genomes, args.validation_shots, args.seed + 700_001, "mps")
    for candidate, metrics in zip(candidates, evaluated):
        candidate["validation"] = metrics["instances"][VALIDATION_NAME]
        candidate["validation_selection_score"] = metrics["selection_score"]
    champions = {"published_lr": candidates[0]}
    for method in ("evolutionary_search", "matched_random_search"):
        method_rows = [row for row in candidates if row["method"] == method]
        champions[method] = max(method_rows, key=lambda row: row["validation_selection_score"])
    payload = {
        "stage": "validation",
        "provenance": provenance(),
        "case": case_metadata(case),
        "shots_per_candidate": args.validation_shots,
        "candidates": candidates,
        "frozen_champions": champions,
    }
    write_json(RESULTS / "validation.json", payload)
    write_json(RESULTS / "frozen_champions.json", champions)
    return payload


def bootstrap_mean_ci(values: np.ndarray, seed: int, draws: int = 20_000) -> list[float]:
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
    return [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))]


def paired_summary(rows: list[dict], method: str, baseline: str, metric: str, seed: int) -> dict:
    method_rows = sorted((r for r in rows if r["method"] == method), key=lambda r: r["replicate"])
    base_rows = sorted((r for r in rows if r["method"] == baseline), key=lambda r: r["replicate"])
    diffs = np.array(
        [m["metrics"][metric] - b["metrics"][metric] for m, b in zip(method_rows, base_rows)],
        dtype=float,
    )
    observed = abs(float(diffs.mean()))
    if len(diffs) <= 20:
        null_means = []
        for mask in range(1 << len(diffs)):
            signs = np.array([1.0 if mask & (1 << i) else -1.0 for i in range(len(diffs))])
            null_means.append(abs(float(np.mean(signs * diffs))))
        sign_flip_p = float(np.mean(np.asarray(null_means) >= observed - 1e-15))
    else:
        rng = np.random.default_rng(seed + 991)
        signs = rng.choice((-1.0, 1.0), size=(100_000, len(diffs)))
        sign_flip_p = float(np.mean(np.abs((signs * diffs).mean(axis=1)) >= observed))
    return {
        "method": method,
        "baseline": baseline,
        "metric": metric,
        "replicates": len(diffs),
        "differences": diffs,
        "mean_difference": float(diffs.mean()),
        "bootstrap_95_ci": bootstrap_mean_ci(diffs, seed),
        "two_sided_paired_sign_flip_p": sign_flip_p,
        "wins_ties_losses": [int((diffs > 0).sum()), int((diffs == 0).sum()), int((diffs < 0).sum())],
    }


def test(args, validation_payload: dict | None = None) -> dict:
    if validation_payload is None:
        validation_payload = json.loads((RESULTS / "validation.json").read_text(encoding="utf-8"))
    champions = validation_payload["frozen_champions"]
    methods = ["published_lr", "evolutionary_search", "matched_random_search"]
    case = prepare_case(TEST_NAME)
    rows = []
    start_replicate = 0
    checkpoint_path = RESULTS / "blind_test_checkpoint.json"
    if args.resume_test and checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        prior_rows = checkpoint.get("rows", [])
        if prior_rows:
            rows = prior_rows
            start_replicate = max(int(row["replicate"]) for row in rows) + 1
            print(f"Resuming blind test at replicate {start_replicate + 1}", flush=True)
    for replicate in range(start_replicate, args.test_replicates):
        seed = args.seed + 900_001 + replicate * 10_007
        print(f"TEST replicate {replicate + 1}/{args.test_replicates} on {TEST_NAME}/{case.reduced_vertices}q MPS", flush=True)
        genomes = np.asarray([champions[m]["genome"] for m in methods], dtype=float)
        evaluated = evaluate_population([case], genomes, args.test_shots, seed, "mps")
        for method, result in zip(methods, evaluated):
            rows.append(
                {
                    "method": method,
                    "replicate": replicate,
                    "seed": seed,
                    "genome": champions[method]["genome"],
                    "metrics": result["instances"][TEST_NAME],
                    "elapsed_batch_seconds": result["elapsed_batch_seconds"],
                }
            )
        payload = {
            "stage": "blind_test",
            "provenance": provenance(),
            "case": case_metadata(case),
            "shots_per_method_replicate": args.test_shots,
            "replicates_planned": args.test_replicates,
            "rows": rows,
            "complete": replicate + 1 == args.test_replicates,
        }
        write_json(checkpoint_path, payload)
    comparisons = []
    for method in ("evolutionary_search", "matched_random_search"):
        for metric in ("bks_rate", "near_bks_rate", "feasible_rate", "quality_mass", "robust_score"):
            comparisons.append(paired_summary(rows, method, "published_lr", metric, args.seed + 77))
    payload["comparisons"] = comparisons
    payload["complete"] = True
    write_json(RESULTS / "blind_test.json", payload)
    return payload


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("train", "validate", "test", "all"), default="all")
    parser.add_argument("--seed", type=int, default=20260803)
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument("--population", type=int, default=20)
    parser.add_argument("--generations", type=int, default=6)
    parser.add_argument("--train-shots", type=int, default=256)
    parser.add_argument("--validation-shots", type=int, default=1000)
    parser.add_argument("--test-shots", type=int, default=1000)
    parser.add_argument("--test-replicates", type=int, default=5)
    parser.add_argument("--resume-test", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    training = validation = None
    if args.stage in ("train", "all"):
        training = train(args)
    if args.stage in ("validate", "all"):
        validation = validate(args, training)
    if args.stage in ("test", "all"):
        test(args, validation)


if __name__ == "__main__":
    main()
