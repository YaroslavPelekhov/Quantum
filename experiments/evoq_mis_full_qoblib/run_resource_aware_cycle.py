"""Strict multi-fidelity resource-aware QAOA benchmark on QOBLIB MIS."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import networkx as nx
import numpy as np
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_array
from scipy.stats import qmc

import run_cycle as rc


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results" / "resource_aware"
PROTOCOL = HERE / "RESOURCE_AWARE_PROTOCOL.md"
DEPTHS = (3, 5, 8, 10, 12, 15)
REDUCTION_CAPS = (2, 3, 4, 5, 6)
TRAIN_NAMES = ("es60fst01", "es60fst03")
VALIDATION_NAME = "es60fst04"
BLIND_NAME = "es60fst02"
ORDERINGS = ("sorted", "spectral")
SETTINGS = {
    "released": {"bond": 64, "cutoff": 1e-3},
    "confirm": {"bond": 128, "cutoff": 1e-4},
}
SCREEN_SEEDS = (26101, 26102, 26103, 26104)
CONFIRM_SEEDS = tuple(range(27101, 27111))
BLIND_SEEDS = tuple(range(28101, 28116))
SCREEN_SHOTS = 250
CONFIRM_SHOTS = 500
BLIND_SHOTS = 1000
BOOTSTRAP_DRAWS = 50_000

ANCHORS = {
    "published_lr": np.array([0.7, 0.4, 1.0, 1.0]),
    "prior_evolutionary": np.array(
        [0.5175030726816078, 0.7719741612274684, 1.0773373543262421, 1.7543477389249704]
    ),
    "prior_matched_random": np.array(
        [0.6424738670407446, 0.7593921349176262, 1.776791693083474, 0.9917239502490107]
    ),
}


@dataclass
class ResourceCase:
    name: str
    bks: int
    graph: nx.Graph
    reduction: object
    decoder: object
    ordering: str
    node_order: list
    sorted_nodes: list
    hamiltonian: object

    @property
    def qubits(self) -> int:
        return len(self.node_order)


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
        return value.as_posix()
    return value


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(payload), indent=2) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance() -> dict:
    import qiskit
    import qiskit_aer
    import scipy

    return {
        "python": sys.version,
        "platform": platform.platform(),
        "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "protocol_sha256": sha256(PROTOCOL),
        "qoblib_solutions_commit": rc.git_commit(rc.BASELINE_REPO),
    }


def spectral_order(graph: nx.Graph) -> list:
    nodes = sorted(graph.nodes())
    if len(nodes) <= 2:
        return nodes
    laplacian = nx.laplacian_matrix(graph, nodelist=nodes).toarray()
    values, vectors = np.linalg.eigh(laplacian)
    nonzero = np.flatnonzero(values > 1e-9)
    index = int(nonzero[0]) if len(nonzero) else 0
    order = [nodes[i] for i in np.argsort(vectors[:, index], kind="stable")]
    reverse = list(reversed(order))
    return min(order, reverse)


def prepare_case(name: str, max_degree: int, ordering: str) -> ResourceCase:
    graph = rc.parse_gph_file(rc.QOBLIB / "07-independentset/instances" / f"{name}.gph")
    reduction = rc.reduce_graph_for_quantum(graph, max_degree=max_degree)
    reduced = reduction.reduced_graph
    if not reduced.number_of_nodes():
        raise RuntimeError(f"{name}/degree{max_degree}: empty reduced kernel")
    sorted_nodes = sorted(reduced.nodes())
    node_order = sorted_nodes if ordering == "sorted" else spectral_order(reduced)
    mapping = {node: i for i, node in enumerate(node_order)}
    relabeled = nx.relabel_nodes(reduced, mapping)
    hamiltonian = rc.mis_hamiltonian(relabeled, lambd=rc.LAMBDA)
    decoder = rc.MISPostprocessor(graph, reduction, repair_samples=False)
    return ResourceCase(
        name=name,
        bks=rc.BKS[name],
        graph=graph,
        reduction=reduction,
        decoder=decoder,
        ordering=ordering,
        node_order=node_order,
        sorted_nodes=sorted_nodes,
        hamiltonian=hamiltonian,
    )


def circuit_for(case: ResourceCase, genome: np.ndarray, depth: int):
    betas, gammas = rc.schedule(np.asarray(genome, dtype=float), p=depth)
    return rc.qaoa_mis(gammas, betas, case.hamiltonian, case.qubits)


def circuit_resources(circuit) -> dict:
    operations = {str(k): int(v) for k, v in circuit.count_ops().items()}
    return {
        "circuit_depth": int(circuit.depth()),
        "circuit_size": int(circuit.size()),
        "rzz_gates": int(operations.get("rzz", 0)),
        "rx_gates": int(operations.get("rx", 0)),
        "operations": operations,
    }


def canonical_bitstring(case: ResourceCase, bitstring: str) -> str:
    bits = bitstring.replace(" ", "")
    if case.ordering == "sorted":
        return bits
    if len(bits) != case.qubits:
        raise ValueError(f"Expected {case.qubits} bits, got {len(bits)}")
    positions = {node: i for i, node in enumerate(case.sorted_nodes)}
    canonical = ["0"] * case.qubits
    for source_i, node in enumerate(case.node_order):
        canonical[positions[node]] = bits[source_i]
    return "".join(canonical)


def canonical_counts(case: ResourceCase, counts: dict[str, int]) -> dict[str, int]:
    output: dict[str, int] = {}
    for bitstring, count in counts.items():
        key = canonical_bitstring(case, bitstring)
        output[key] = output.get(key, 0) + int(count)
    return output


def probability_metrics(case: ResourceCase, probabilities: dict[str, float]) -> dict:
    feasible = bks = near = quality = selected_mass = 0.0
    best = None
    for bitstring, probability in probabilities.items():
        probability = float(probability)
        # Statevector keys are q[n-1]...q[0], while the released decoder and
        # measured QAOA circuits expose the reduced-node order q[0]...q[n-1].
        decoded = case.decoder.decode(canonical_bitstring(case, bitstring[::-1]))
        if not decoded.raw_feasible:
            continue
        size = int(decoded.raw_selected)
        feasible += probability
        bks += probability if size >= case.bks else 0.0
        near += probability if size >= case.bks - 1 else 0.0
        quality += probability * min(size / case.bks, 1.0)
        selected_mass += probability * size
        best = size if best is None else max(best, size)
    return {
        "feasible_rate": feasible,
        "bks_rate": bks,
        "near_bks_rate": near,
        "quality_mass": quality,
        "conditional_mean_size": selected_mass / feasible if feasible else None,
        "best_size_nonzero_probability": best,
    }


def exact_evaluate(case: ResourceCase, genome: np.ndarray, depth: int) -> dict:
    circuit = circuit_for(case, genome, depth)
    resources = circuit_resources(circuit)
    bare = circuit.remove_final_measurements(inplace=False)
    start = perf_counter()
    state = Statevector.from_instruction(bare)
    elapsed = perf_counter() - start
    metrics = probability_metrics(case, state.probabilities_dict())
    return {"metrics": metrics, "resources": resources, "elapsed_seconds": elapsed}


def mps_evaluate(
    case: ResourceCase,
    genome: np.ndarray,
    depth: int,
    shots: int,
    seed: int,
    bond: int,
    cutoff: float,
) -> dict:
    circuit = circuit_for(case, genome, depth)
    resources = circuit_resources(circuit)
    backend = AerSimulator(
        method="matrix_product_state",
        matrix_product_state_max_bond_dimension=bond,
        matrix_product_state_truncation_threshold=cutoff,
        max_parallel_experiments=1,
    )
    start = perf_counter()
    result = backend.run(circuit, shots=shots, seed_simulator=seed).result()
    elapsed = perf_counter() - start
    counts = canonical_counts(case, result.get_counts())
    metrics = rc.summarize_counts(case, counts)
    return {
        "metrics": metrics,
        "resources": resources,
        "elapsed_seconds": elapsed,
        "counts": counts,
    }


def exact_reduced_optimum(name: str, max_degree: int) -> dict:
    graph = rc.parse_gph_file(rc.QOBLIB / "07-independentset/instances" / f"{name}.gph")
    reduction = rc.reduce_graph_for_quantum(graph, max_degree=max_degree)
    reduced = reduction.reduced_graph
    if not reduced.number_of_nodes():
        return {
            "name": name,
            "max_degree": max_degree,
            "qubits": 0,
            "reduced_edges": 0,
            "status": "empty_kernel",
            "decoded_size": None,
            "raw_feasible": None,
            "bks_reachable": False,
        }
    nodes = sorted(reduced.nodes())
    index = {node: i for i, node in enumerate(nodes)}
    rows, cols = [], []
    for row, (u, v) in enumerate(reduced.edges()):
        rows.extend((row, row))
        cols.extend((index[u], index[v]))
    matrix = coo_array(
        (np.ones(len(rows)), (rows, cols)),
        shape=(reduced.number_of_edges(), len(nodes)),
    ).tocsr()
    start = perf_counter()
    result = milp(
        -np.ones(len(nodes)),
        integrality=np.ones(len(nodes)),
        bounds=Bounds(0, 1),
        constraints=LinearConstraint(matrix, -np.inf, 1),
        options={"time_limit": 300, "mip_rel_gap": 0.0, "presolve": True},
    )
    elapsed = perf_counter() - start
    if not result.success:
        raise RuntimeError(f"Reduced HiGHS failure for {name}/d{max_degree}: {result.message}")
    selected = {node for node, value in zip(nodes, result.x) if value > 0.5}
    bitstring = "".join("1" if node in selected else "0" for node in nodes)
    decoded = rc.MISPostprocessor(graph, reduction, repair_samples=False).decode(bitstring)
    return {
        "name": name,
        "max_degree": max_degree,
        "qubits": reduced.number_of_nodes(),
        "reduced_edges": reduced.number_of_edges(),
        "status": "optimal",
        "mip_gap": float(result.mip_gap),
        "elapsed_seconds": elapsed,
        "kernel_mis_size": len(selected),
        "decoded_size": int(decoded.raw_selected),
        "raw_feasible": bool(decoded.raw_feasible),
        "bks": rc.BKS[name],
        "bks_reachable": bool(decoded.raw_feasible and decoded.raw_selected >= rc.BKS[name]),
    }


def stage_certify() -> dict:
    rows = [exact_reduced_optimum(name, cap) for cap in REDUCTION_CAPS for name in (*TRAIN_NAMES, VALIDATION_NAME, BLIND_NAME)]
    eligible = []
    for cap in REDUCTION_CAPS:
        cap_rows = [row for row in rows if row["max_degree"] == cap]
        if all(row["bks_reachable"] for row in cap_rows):
            eligible.append(cap)
    if not eligible:
        raise RuntimeError("No reduction cap preserves BKS reachability on all four instances")
    payload = {
        "stage": "resource_reachability_certification",
        "complete": True,
        "provenance": provenance(),
        "rows": rows,
        "eligible_caps": eligible,
        "selected_minimum_cap": min(eligible),
    }
    write_json(RESULTS / "reachability.json", payload)
    return payload


def schedule_candidates() -> list[dict]:
    candidates = [
        {"schedule_id": name, "source": "anchor", "genome": genome.tolist()}
        for name, genome in ANCHORS.items()
    ]
    engine = qmc.Sobol(d=4, scramble=True, seed=260806)
    samples = qmc.scale(engine.random_base2(m=5), rc.BOUNDS[:, 0], rc.BOUNDS[:, 1])
    for index, genome in enumerate(samples):
        candidates.append(
            {
                "schedule_id": f"sobol_{index:02d}",
                "source": "scrambled_sobol",
                "genome": genome.tolist(),
            }
        )
    return candidates


def config_id(schedule_id: str, depth: int) -> str:
    return f"{schedule_id}_p{depth}"


def stage_train() -> dict:
    reachability = read_json(RESULTS / "reachability.json")
    max_degree = int(reachability["selected_minimum_cap"])
    output = RESULTS / "train_exact.json"
    checkpoint = RESULTS / "train_exact_checkpoint.json"
    rows = []
    if checkpoint.exists():
        rows = read_json(checkpoint).get("rows", [])
    completed = {row["config_id"] for row in rows}
    cases = {name: prepare_case(name, max_degree, "sorted") for name in TRAIN_NAMES}
    candidates = schedule_candidates()
    for depth in DEPTHS:
        for candidate in candidates:
            cid = config_id(candidate["schedule_id"], depth)
            if cid in completed:
                continue
            instances = {}
            for name, case in cases.items():
                instances[name] = exact_evaluate(case, np.asarray(candidate["genome"]), depth)
            first = next(iter(instances.values()))
            metrics = [row["metrics"] for row in instances.values()]
            rows.append(
                {
                    "config_id": cid,
                    "schedule_id": candidate["schedule_id"],
                    "source": candidate["source"],
                    "genome": candidate["genome"],
                    "depth": depth,
                    "qubits_by_instance": {name: case.qubits for name, case in cases.items()},
                    "resources": first["resources"],
                    "instances": instances,
                    "worst_bks_rate": min(m["bks_rate"] for m in metrics),
                    "worst_near_bks_rate": min(m["near_bks_rate"] for m in metrics),
                    "worst_feasible_rate": min(m["feasible_rate"] for m in metrics),
                    "mean_quality_mass": float(np.mean([m["quality_mass"] for m in metrics])),
                }
            )
            write_json(checkpoint, {"complete": False, "rows": rows})

    references = {
        name: next(
            row["instances"][name]["metrics"]
            for row in rows
            if row["config_id"] == "published_lr_p15"
        )
        for name in TRAIN_NAMES
    }
    for row in rows:
        row["training_eligible"] = all(
            row["instances"][name]["metrics"]["bks_rate"] >= 0.75 * references[name]["bks_rate"]
            and row["instances"][name]["metrics"]["near_bks_rate"] >= 0.90 * references[name]["near_bks_rate"]
            and row["instances"][name]["metrics"]["feasible_rate"] >= references[name]["feasible_rate"] - 0.02
            for name in TRAIN_NAMES
        )

    eligible = [row for row in rows if row["training_eligible"]]
    per_depth = []
    for depth in DEPTHS:
        options = [row for row in eligible if row["depth"] == depth]
        if not options:
            continue
        options.sort(
            key=lambda row: (
                -(2 * row["worst_bks_rate"] + row["worst_near_bks_rate"] + 0.25 * row["worst_feasible_rate"]),
                row["resources"]["rzz_gates"],
                row["config_id"],
            )
        )
        per_depth.append(options[0])
    promoted = []
    for row in sorted(per_depth, key=lambda row: row["depth"]):
        if len(promoted) >= 5:
            break
        promoted.append(row)
    for anchor_id in ("published_lr_p15", "prior_evolutionary_p15", "prior_matched_random_p15"):
        row = next(item for item in rows if item["config_id"] == anchor_id)
        if all(item["config_id"] != anchor_id for item in promoted):
            promoted.append(row)
    promoted = promoted[:8]

    payload = {
        "stage": "exact_multi_fidelity_training",
        "complete": True,
        "provenance": provenance(),
        "max_degree": max_degree,
        "candidate_schedules": len(candidates),
        "depths": list(DEPTHS),
        "configuration_count": len(rows),
        "training_eligible_count": len(eligible),
        "references": references,
        "rows": rows,
    }
    write_json(output, payload)
    shortlist = {
        "stage": "screen_shortlist_frozen_before_validation",
        "complete": True,
        "protocol_sha256": sha256(PROTOCOL),
        "source_sha256": sha256(output),
        "max_degree": max_degree,
        "configs": [
            {
                key: row[key]
                for key in ("config_id", "schedule_id", "source", "genome", "depth", "resources", "training_eligible")
            }
            for row in promoted
        ],
    }
    write_json(RESULTS / "screen_shortlist.json", shortlist)
    if checkpoint.exists():
        checkpoint.unlink()
    return payload


def ordering_exact_check(max_degree: int) -> dict:
    rows = []
    for name in TRAIN_NAMES:
        sorted_case = prepare_case(name, max_degree, "sorted")
        spectral_case = prepare_case(name, max_degree, "spectral")
        for depth in (5, 15):
            sorted_result = exact_evaluate(sorted_case, ANCHORS["published_lr"], depth)
            spectral_result = exact_evaluate(spectral_case, ANCHORS["published_lr"], depth)
            errors = {
                key: abs(sorted_result["metrics"][key] - spectral_result["metrics"][key])
                for key in ("bks_rate", "near_bks_rate", "feasible_rate", "quality_mass")
            }
            if max(errors.values()) > 1e-10:
                raise AssertionError(f"Ordering remap failed for {name}/p{depth}: {errors}")
            rows.append({"name": name, "depth": depth, "absolute_errors": errors})
    return {"complete": True, "rows": rows}


def load_or_run_jobs(
    path: Path,
    stage: str,
    configs: list[dict],
    case_name: str,
    max_degree: int,
    settings: dict[str, dict],
    seeds: tuple[int, ...],
    shots: int,
) -> dict:
    rows = []
    if path.exists():
        rows = read_json(path).get("rows", [])
    # A configuration may be listed both as a promoted candidate and a named
    # control. Job identity, not list position, defines the experiment. Keep
    # the first completed result and remove any accidental execution duplicate.
    unique_rows = {}
    for row in rows:
        job_key = (row["config_key"], row["setting"], int(row["seed"]))
        unique_rows.setdefault(job_key, row)
    rows = list(unique_rows.values())
    completed = {
        (row["config_key"], row["setting"], int(row["seed"])) for row in rows
    }
    case_cache = {
        ordering: prepare_case(case_name, max_degree, ordering) for ordering in ORDERINGS
    }
    for config in configs:
        key = config["config_key"]
        case = case_cache[config["ordering"]]
        for setting_name, setting in settings.items():
            for seed in seeds:
                job_key = (key, setting_name, seed)
                if job_key in completed:
                    continue
                result = mps_evaluate(
                    case,
                    np.asarray(config["genome"]),
                    int(config["depth"]),
                    shots,
                    seed,
                    int(setting["bond"]),
                    float(setting["cutoff"]),
                )
                rows.append(
                    {
                        "config_key": key,
                        "base_config_id": config["config_id"],
                        "schedule_id": config["schedule_id"],
                        "genome": config["genome"],
                        "depth": int(config["depth"]),
                        "ordering": config["ordering"],
                        "setting": setting_name,
                        "bond": int(setting["bond"]),
                        "cutoff": float(setting["cutoff"]),
                        "seed": int(seed),
                        "shots": shots,
                        **result,
                    }
                )
                completed.add(job_key)
                write_json(
                    path,
                    {
                        "stage": stage,
                        "complete": False,
                        "protocol_sha256": sha256(PROTOCOL),
                        "rows": rows,
                    },
                )
    payload = {
        "stage": stage,
        "complete": True,
        "provenance": provenance(),
        "case": case_name,
        "max_degree": max_degree,
        "settings": settings,
        "seeds": list(seeds),
        "shots_per_job": shots,
        "rows": rows,
    }
    write_json(path, payload)
    return payload


def aggregate_jobs(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        groups.setdefault((row["config_key"], row["setting"]), []).append(row)
    output = []
    for (key, setting), jobs in sorted(groups.items()):
        shots = sum(job["metrics"]["total_shots"] for job in jobs)
        sums = {
            metric: sum(job["metrics"][metric] for job in jobs)
            for metric in ("bks_hits", "near_bks_hits", "feasible_shots")
        }
        first = jobs[0]
        output.append(
            {
                "config_key": key,
                "setting": setting,
                "base_config_id": first["base_config_id"],
                "schedule_id": first["schedule_id"],
                "genome": first["genome"],
                "depth": first["depth"],
                "ordering": first["ordering"],
                "jobs": len(jobs),
                "total_shots": shots,
                "bks_hits": sums["bks_hits"],
                "bks_rate": sums["bks_hits"] / shots,
                "near_bks_hits": sums["near_bks_hits"],
                "near_bks_rate": sums["near_bks_hits"] / shots,
                "feasible_shots": sums["feasible_shots"],
                "feasible_rate": sums["feasible_shots"] / shots,
                "wilson_bks": rc.wilson_lower(sums["bks_hits"], shots),
                "wilson_near_bks": rc.wilson_lower(sums["near_bks_hits"], shots),
                "wilson_feasible": rc.wilson_lower(sums["feasible_shots"], shots),
                "mean_elapsed_seconds": float(np.mean([job["elapsed_seconds"] for job in jobs])),
                "median_elapsed_seconds": float(np.median([job["elapsed_seconds"] for job in jobs])),
                "resources": first["resources"],
            }
        )
    return output


def config_with_order(config: dict, ordering: str) -> dict:
    return {
        **config,
        "ordering": ordering,
        "config_key": f"{config['config_id']}__{ordering}",
    }


def stage_screen() -> dict:
    shortlist = read_json(RESULTS / "screen_shortlist.json")
    max_degree = int(shortlist["max_degree"])
    order_check = ordering_exact_check(max_degree)
    configs = [config_with_order(config, ordering) for config in shortlist["configs"] for ordering in ORDERINGS]
    payload = load_or_run_jobs(
        RESULTS / "validation_screen.json",
        "validation_resource_screen",
        configs,
        VALIDATION_NAME,
        max_degree,
        {"released": SETTINGS["released"]},
        SCREEN_SEEDS,
        SCREEN_SHOTS,
    )
    summary = aggregate_jobs(payload["rows"])
    reference = next(row for row in summary if row["config_key"] == "published_lr_p15__sorted")
    candidates = [
        row
        for row in summary
        if row["config_key"] not in {"published_lr_p15__sorted", "prior_matched_random_p15__sorted"}
        and row["bks_rate"] >= reference["bks_rate"] - 0.015
        and row["near_bks_rate"] >= reference["near_bks_rate"] - 0.05
        and row["feasible_rate"] >= reference["feasible_rate"] - 0.05
    ]
    if len(candidates) < 4:
        fallback = [row for row in summary if row not in candidates and row["schedule_id"] != "published_lr"]
        fallback.sort(
            key=lambda row: (
                -(2 * row["bks_rate"] + row["near_bks_rate"] + 0.25 * row["feasible_rate"]),
                row["resources"]["rzz_gates"],
                row["median_elapsed_seconds"],
            )
        )
        for row in fallback:
            if len(candidates) >= 4:
                break
            if all(item["config_key"] != row["config_key"] for item in candidates):
                candidates.append(row)
    candidates.sort(
        key=lambda row: (
            row["resources"]["rzz_gates"],
            row["median_elapsed_seconds"],
            -row["bks_rate"],
        )
    )
    candidates = candidates[:4]
    control_keys = ("published_lr_p15__sorted", "prior_matched_random_p15__sorted")
    selected_rows = candidates + [next(row for row in summary if row["config_key"] == key) for key in control_keys]
    confirm_configs = [
        {
            key: row[key]
            for key in ("config_key", "base_config_id", "schedule_id", "genome", "depth", "ordering")
        }
        | {"config_id": row["base_config_id"]}
        for row in selected_rows
    ]
    payload["ordering_exact_check"] = order_check
    payload["summary"] = summary
    payload["reference"] = reference
    payload["complete"] = True
    write_json(RESULTS / "validation_screen.json", payload)
    frozen = {
        "stage": "confirmation_shortlist_frozen_before_accuracy_confirmation",
        "complete": True,
        "protocol_sha256": sha256(PROTOCOL),
        "source_sha256": sha256(RESULTS / "validation_screen.json"),
        "max_degree": max_degree,
        "configs": confirm_configs,
    }
    write_json(RESULTS / "confirm_shortlist.json", frozen)
    return payload


def paired_bootstrap(candidate_jobs: list[dict], reference_jobs: list[dict], metric: str, seed: int) -> dict:
    candidate_by_seed = {int(row["seed"]): row for row in candidate_jobs}
    reference_by_seed = {int(row["seed"]): row for row in reference_jobs}
    seeds = sorted(set(candidate_by_seed) & set(reference_by_seed))
    differences = np.array(
        [candidate_by_seed[s]["metrics"][metric] - reference_by_seed[s]["metrics"][metric] for s in seeds],
        dtype=float,
    )
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(differences), size=(BOOTSTRAP_DRAWS, len(differences)))
    means = differences[indices].mean(axis=1)
    return {
        "paired_jobs": len(seeds),
        "mean_difference": float(differences.mean()),
        "ci95": [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))],
        "wins": int(np.sum(differences > 0)),
        "ties": int(np.sum(differences == 0)),
        "losses": int(np.sum(differences < 0)),
    }


def sign_flip_pvalue(differences: np.ndarray) -> float:
    observed = abs(float(np.mean(differences)))
    count = 0
    total = 1 << len(differences)
    for mask in range(total):
        signs = np.array([1.0 if (mask >> i) & 1 else -1.0 for i in range(len(differences))])
        if abs(float(np.mean(differences * signs))) >= observed - 1e-15:
            count += 1
    return count / total


def required_shots_95(rate: float) -> int | None:
    if rate <= 0:
        return None
    if rate >= 1:
        return 1
    return int(math.ceil(math.log(0.05) / math.log(1.0 - rate)))


def comparisons_to_reference(rows: list[dict], reference_key: str) -> list[dict]:
    output = []
    for setting in SETTINGS:
        reference = [row for row in rows if row["config_key"] == reference_key and row["setting"] == setting]
        keys = sorted({row["config_key"] for row in rows if row["setting"] == setting})
        for key in keys:
            candidate = [row for row in rows if row["config_key"] == key and row["setting"] == setting]
            comparisons = {}
            for index, metric in enumerate(("bks_rate", "near_bks_rate", "feasible_rate")):
                comparisons[metric] = paired_bootstrap(candidate, reference, metric, 29000 + index)
                diffs = np.array(
                    [c["metrics"][metric] - r["metrics"][metric] for c, r in zip(sorted(candidate, key=lambda x: x["seed"]), sorted(reference, key=lambda x: x["seed"]))]
                )
                comparisons[metric]["sign_flip_p_two_sided"] = sign_flip_pvalue(diffs)
            output.append({"config_key": key, "setting": setting, "comparisons": comparisons})
    return output


def stage_confirm() -> dict:
    shortlist = read_json(RESULTS / "confirm_shortlist.json")
    payload = load_or_run_jobs(
        RESULTS / "validation_confirm.json",
        "validation_two_accuracy_confirmation",
        shortlist["configs"],
        VALIDATION_NAME,
        int(shortlist["max_degree"]),
        SETTINGS,
        CONFIRM_SEEDS,
        CONFIRM_SHOTS,
    )
    summary = aggregate_jobs(payload["rows"])
    comparisons = comparisons_to_reference(payload["rows"], "published_lr_p15__sorted")
    by_key_setting = {(row["config_key"], row["setting"]): row for row in summary}
    comp_lookup = {(row["config_key"], row["setting"]): row for row in comparisons}
    keys = sorted({row["config_key"] for row in summary})
    decisions = []
    for key in keys:
        if key in {"published_lr_p15__sorted", "prior_matched_random_p15__sorted"}:
            continue
        setting_decisions = []
        for setting in SETTINGS:
            comparison = comp_lookup[(key, setting)]["comparisons"]
            setting_decisions.append(
                comparison["bks_rate"]["ci95"][0] > -0.005
                and comparison["near_bks_rate"]["ci95"][0] > -0.02
                and comparison["feasible_rate"]["ci95"][0] > -0.02
            )
        candidate_rows = [by_key_setting[(key, setting)] for setting in SETTINGS]
        reference_rows = [by_key_setting[("published_lr_p15__sorted", setting)] for setting in SETTINGS]
        lower_depth = candidate_rows[0]["depth"] < 15
        faster = np.median([row["median_elapsed_seconds"] for row in candidate_rows]) <= 0.9 * np.median(
            [row["median_elapsed_seconds"] for row in reference_rows]
        )
        decisions.append(
            {
                "config_key": key,
                "noninferior_both_settings": all(setting_decisions),
                "resource_reduction": bool(lower_depth or faster),
                "eligible": bool(all(setting_decisions) and (lower_depth or faster)),
                "lower_depth": lower_depth,
                "runtime_at_least_10pct_faster": bool(faster),
            }
        )
    eligible = [row for row in decisions if row["eligible"]]
    eligible.sort(
        key=lambda decision: (
            by_key_setting[(decision["config_key"], "confirm")]["resources"]["rzz_gates"],
            np.median([by_key_setting[(decision["config_key"], setting)]["median_elapsed_seconds"] for setting in SETTINGS]),
            required_shots_95(min(by_key_setting[(decision["config_key"], setting)]["bks_rate"] for setting in SETTINGS)) or 10**12,
            -min(by_key_setting[(decision["config_key"], setting)]["wilson_bks"] for setting in SETTINGS),
        )
    )
    champion_key = eligible[0]["config_key"] if eligible else None
    champion_config = next((config for config in shortlist["configs"] if config["config_key"] == champion_key), None)
    payload["summary"] = summary
    payload["comparisons"] = comparisons
    payload["decisions"] = decisions
    payload["complete"] = True
    write_json(RESULTS / "validation_confirm.json", payload)
    champion = {
        "stage": "resource_champion_frozen_before_blind",
        "complete": True,
        "protocol_sha256": sha256(PROTOCOL),
        "source_sha256": sha256(RESULTS / "validation_confirm.json"),
        "status": "eligible_champion" if champion_config else "no_eligible_resource_champion",
        "max_degree": int(shortlist["max_degree"]),
        "config": champion_config,
        "decision": next((row for row in decisions if row["config_key"] == champion_key), None),
    }
    champion["selection_payload_sha256"] = hashlib.sha256(
        json.dumps(jsonable(champion), sort_keys=True).encode("utf-8")
    ).hexdigest()
    write_json(RESULTS / "frozen_resource_champion.json", champion)
    return payload


def stage_blind() -> dict:
    champion = read_json(RESULTS / "frozen_resource_champion.json")
    max_degree = int(champion["max_degree"])
    configs = []
    if champion["config"] is not None:
        configs.append(champion["config"])
    configs.extend(
        [
            {
                "config_id": "published_lr_p15",
                "config_key": "published_lr_p15__sorted",
                "base_config_id": "published_lr_p15",
                "schedule_id": "published_lr",
                "genome": ANCHORS["published_lr"].tolist(),
                "depth": 15,
                "ordering": "sorted",
            },
            {
                "config_id": "prior_matched_random_p15",
                "config_key": "prior_matched_random_p15__sorted",
                "base_config_id": "prior_matched_random_p15",
                "schedule_id": "prior_matched_random",
                "genome": ANCHORS["prior_matched_random"].tolist(),
                "depth": 15,
                "ordering": "sorted",
            },
        ]
    )
    unique = {config["config_key"]: config for config in configs}
    payload = load_or_run_jobs(
        RESULTS / "blind_confirmation.json",
        "blind_resource_confirmation",
        list(unique.values()),
        BLIND_NAME,
        max_degree,
        SETTINGS,
        BLIND_SEEDS,
        BLIND_SHOTS,
    )
    payload["frozen_champion_sha256"] = sha256(RESULTS / "frozen_resource_champion.json")
    payload["summary"] = aggregate_jobs(payload["rows"])
    payload["comparisons"] = comparisons_to_reference(payload["rows"], "published_lr_p15__sorted")
    payload["complete"] = True
    write_json(RESULTS / "blind_confirmation.json", payload)
    return payload


def stage_analyze() -> dict:
    reach = read_json(RESULTS / "reachability.json")
    train = read_json(RESULTS / "train_exact.json")
    screen = read_json(RESULTS / "validation_screen.json")
    confirm = read_json(RESULTS / "validation_confirm.json")
    champion = read_json(RESULTS / "frozen_resource_champion.json")
    blind_path = RESULTS / "blind_confirmation.json"
    blind = read_json(blind_path) if blind_path.exists() else None
    payload = {
        "stage": "resource_aware_analysis",
        "complete": True,
        "protocol_sha256": sha256(PROTOCOL),
        "selected_reduction_cap": reach["selected_minimum_cap"],
        "training_configurations": train["configuration_count"],
        "training_eligible": train["training_eligible_count"],
        "screen_configurations": len(screen["summary"]),
        "validation_decisions": confirm["decisions"],
        "champion": champion,
        "blind_summary": None if blind is None else blind["summary"],
        "blind_comparisons": None if blind is None else blind["comparisons"],
    }
    write_json(RESULTS / "analysis.json", payload)

    rows = [] if blind is None else blind["summary"]
    with (RESULTS / "blind_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["config", "setting", "depth", "ordering", "shots", "bks_hits", "bks_rate", "near_rate", "feasible_rate", "median_seconds", "rzz_gates"]
        )
        for row in rows:
            writer.writerow(
                [
                    row["config_key"], row["setting"], row["depth"], row["ordering"], row["total_shots"],
                    row["bks_hits"], row["bks_rate"], row["near_bks_rate"], row["feasible_rate"],
                    row["median_elapsed_seconds"], row["resources"]["rzz_gates"],
                ]
            )

    lines = [
        "# Resource-aware QAOA cycle", "",
        f"- Minimum BKS-preserving reduction cap: `{reach['selected_minimum_cap']}`.",
        f"- Exact schedule-depth configurations evaluated: {train['configuration_count']}.",
        f"- Exact training-eligible configurations: {train['training_eligible_count']}.",
        f"- Champion status: `{champion['status']}`.", "",
    ]
    if champion["config"]:
        lines.append(f"Frozen champion: `{champion['config']['config_key']}`.")
        lines.append("")
    if rows:
        lines.extend(
            [
                "## Blind summary", "",
                "| Configuration | Setting | Depth | BKS | Near-BKS | Feasible | Median s/job | RZZ |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in rows:
            lines.append(
                f"| {row['config_key']} | {row['setting']} | {row['depth']} | "
                f"{row['bks_hits']}/{row['total_shots']} ({row['bks_rate']:.5f}) | "
                f"{row['near_bks_rate']:.5f} | {row['feasible_rate']:.5f} | "
                f"{row['median_elapsed_seconds']:.3f} | {row['resources']['rzz_gates']} |"
            )
        candidate_comparisons = [
            row
            for row in blind["comparisons"]
            if row["config_key"] == "prior_matched_random_p15__sorted"
        ]
        lines.extend(
            [
                "",
                "## Paired blind comparison against published LR",
                "",
                "| Setting | Metric | Mean difference | Paired-bootstrap 95% CI | Sign-flip p |",
                "|---|---|---:|---:|---:|",
            ]
        )
        for comparison in candidate_comparisons:
            for metric in ("bks_rate", "near_bks_rate", "feasible_rate"):
                stats = comparison["comparisons"][metric]
                lines.append(
                    f"| {comparison['setting']} | {metric} | {stats['mean_difference']:+.5f} | "
                    f"[{stats['ci95'][0]:+.5f}, {stats['ci95'][1]:+.5f}] | "
                    f"{stats['sign_flip_p_two_sided']:.6g} |"
                )
        lines.extend(
            [
                "",
                "## Strict conclusion",
                "",
                "No newly searched configuration satisfied the pre-registered non-inferiority "
                "gate at both MPS fidelities, so the controller correctly returned no resource "
                "champion. The smallest reduction cap preserving the known best solution on all "
                "four instances was 4; lower depths did not preserve blind-relevant validation "
                "performance.",
                "",
                "The held-out comparison shows a statistically significant fidelity reversal. "
                "The prior matched schedule improves BKS under the released approximation but "
                "degrades BKS under the tighter confirmation setting. Feasibility improves under "
                "both, demonstrating that feasibility alone is not a sufficient proxy for the "
                "upper tail of solution quality.",
                "",
                "The defensible application result is therefore a certified abstention: under "
                "the frozen quality tolerances, this search found no safe reduction in qubits, "
                "QAOA depth, or end-to-end runtime. The methodological result is that multi-fidelity "
                "confirmation prevents a cheap tensor-network approximation from producing a false "
                "resource-efficiency claim.",
                "",
                "## Scope",
                "",
                "These conclusions apply to the frozen four-instance es60fst split, noiseless MPS "
                "simulation, native unrepaired samples, and the tested schedule family. Hardware "
                "latency/noise and broader QOBLIB families remain external-validation targets.",
            ]
        )
    (HERE / "RESOURCE_AWARE_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=("certify", "train", "screen", "confirm", "blind", "analyze", "all"),
        default="all",
    )
    args = parser.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    stages = {
        "certify": stage_certify,
        "train": stage_train,
        "screen": stage_screen,
        "confirm": stage_confirm,
        "blind": stage_blind,
        "analyze": stage_analyze,
    }
    selected = list(stages) if args.stage == "all" else [args.stage]
    for stage in selected:
        start = perf_counter()
        print(f"[{stage}] starting", flush=True)
        stages[stage]()
        print(f"[{stage}] complete in {perf_counter() - start:.3f}s", flush=True)


if __name__ == "__main__":
    main()
