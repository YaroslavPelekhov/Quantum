"""Frozen cross-family external-validity cycle for resource-aware QAOA."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from time import perf_counter

import numpy as np

import run_cycle as rc
import run_resource_aware_cycle as rr


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results" / "external_validity"
PROTOCOL = HERE / "EXTERNAL_VALIDITY_PROTOCOL.md"
SOLUTIONS_README = rc.QOBLIB / "07-independentset" / "solutions" / "README.md"

DEPTH = 15
SETTINGS = {
    "released": {"bond": 64, "cutoff": 1e-3},
    "confirm": {"bond": 128, "cutoff": 1e-4},
}
CORE_CASES = {
    "aves-sparrow-social": 20,
    "chesapeake": 12,
    "football": 10,
    "ibm32": 8,
    "johnson8-2-4": 16,
    "karate": 4,
}
SCALE_CASES = {"hamming6-4": 24, "sloane_1dc_64": 24}
EXACT_CASES = {"chesapeake": 12, "football": 10, "ibm32": 8, "karate": 4}
LOWER_CAPS = {
    "aves-sparrow-social": 16,
    "chesapeake": 10,
    "football": 8,
    "ibm32": 6,
    "johnson8-2-4": 12,
    "karate": 3,
    "hamming6-4": 20,
    "sloane_1dc_64": 20,
}
BOUNDARY_CAPS = {
    "C125-9": (12, 16),
    "c-fat200-1": (12, 16),
    "gen200_p0-9_44": (16, 20, 24),
    "sloane_1dc_128": (20, 24, 28, 32),
    "sloane_1zc_128": (16, 20),
    "brock200-2": (32, 64, 96, 128),
}
CORE_SEEDS = tuple(range(31001, 31006))
SCALE_SEEDS = tuple(range(32001, 32004))
CORE_SHOTS = 500
SCALE_SHOTS = 250
BOOTSTRAP_DRAWS = 50_000

METHODS = {
    "published_lr": [0.7, 0.4, 1.0, 1.0],
    "prior_evolutionary": [
        0.5175030726816078,
        0.7719741612274684,
        1.0773373543262421,
        1.7543477389249704,
    ],
    "prior_matched_random": [
        0.6424738670407446,
        0.7593921349176262,
        1.776791693083474,
        0.9917239502490107,
    ],
}


def load_bks() -> dict[str, int]:
    values = {}
    for line in SOLUTIONS_README.read_text(encoding="utf-8").splitlines():
        parts = [part.strip() for part in line.split("|")]
        if len(parts) > 3 and parts[2].isdigit():
            values[parts[1]] = int(parts[2])
    return values


BKS = load_bks()
rc.BKS.update(BKS)


def jsonable(value):
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
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


def certification_row(name: str, cap: int) -> dict:
    graph = rc.parse_gph_file(rc.QOBLIB / "07-independentset" / "instances" / f"{name}.gph")
    reduction = rc.reduce_graph_for_quantum(graph, max_degree=cap)
    reduced = reduction.reduced_graph
    base = {
        "name": name,
        "bks": BKS[name],
        "max_degree": cap,
        "original_vertices": graph.number_of_nodes(),
        "original_edges": graph.number_of_edges(),
        "qubits": reduced.number_of_nodes(),
        "reduced_edges": reduced.number_of_edges(),
        "heuristically_pruned_vertices": len(reduction.pruned_nodes),
        "forced_selected_vertices": len(reduction.nodes_to_add),
    }
    if not reduced.number_of_nodes():
        decoded = rc.MISPostprocessor(graph, reduction, repair_samples=False).decode("")
        return {
            **base,
            "status": "empty_deterministic_kernel",
            "decoded_size": int(decoded.raw_selected),
            "raw_feasible": bool(decoded.raw_feasible),
            "bks_reachable": bool(decoded.raw_feasible and decoded.raw_selected >= BKS[name]),
            "elapsed_seconds": 0.0,
        }
    result = rr.exact_reduced_optimum(name, cap)
    return {**base, **result}


def stage_certify() -> dict:
    path = RESULTS / "reachability.json"
    rows = read_json(path).get("rows", []) if path.exists() else []
    unique = {(row["name"], int(row["max_degree"])): row for row in rows}
    jobs = []
    for name, cap in {**CORE_CASES, **SCALE_CASES}.items():
        jobs.extend(((name, LOWER_CAPS[name], "lower_control"), (name, cap, "selected")))
    for name, caps in BOUNDARY_CAPS.items():
        jobs.extend((name, cap, "boundary") for cap in caps)
    for name, cap, cohort in jobs:
        key = (name, cap)
        if key in unique:
            continue
        row = {**certification_row(name, cap), "cohort": cohort}
        unique[key] = row
        write_json(
            path,
            {
                "stage": "external_reachability_certification",
                "complete": False,
                "protocol_sha256": sha256(PROTOCOL),
                "rows": list(unique.values()),
            },
        )
    rows = sorted(unique.values(), key=lambda row: (row["name"], row["max_degree"]))
    for name, cap in {**CORE_CASES, **SCALE_CASES}.items():
        row = unique[(name, cap)]
        if not row["bks_reachable"] or row["qubits"] <= 0 or row["qubits"] > 64:
            raise RuntimeError(f"Frozen quantum cohort certification failed: {name}/cap{cap}")
    payload = {
        "stage": "external_reachability_certification",
        "complete": True,
        "provenance": provenance(),
        "quantum_cases": {**CORE_CASES, **SCALE_CASES},
        "boundary_caps": BOUNDARY_CAPS,
        "rows": rows,
    }
    write_json(path, payload)
    return payload


def exact_identity(row: dict) -> tuple:
    return row["case"], row["method"], row["ordering"]


def stage_exact() -> dict:
    path = RESULTS / "exact_statevector.json"
    rows = read_json(path).get("rows", []) if path.exists() else []
    unique = {exact_identity(row): row for row in rows}
    for name, cap in EXACT_CASES.items():
        for method, genome in METHODS.items():
            for ordering in ("sorted", "spectral"):
                key = (name, method, ordering)
                if key in unique:
                    continue
                case = rr.prepare_case(name, cap, ordering)
                result = rr.exact_evaluate(case, np.asarray(genome), DEPTH)
                row = {
                    "case": name,
                    "bks": BKS[name],
                    "max_degree": cap,
                    "qubits": case.qubits,
                    "method": method,
                    "genome": genome,
                    "depth": DEPTH,
                    "ordering": ordering,
                    **result,
                }
                unique[key] = row
                write_json(
                    path,
                    {
                        "stage": "external_exact_statevector",
                        "complete": False,
                        "protocol_sha256": sha256(PROTOCOL),
                        "rows": list(unique.values()),
                    },
                )
    rows = sorted(unique.values(), key=exact_identity)
    max_ordering_error = 0.0
    for name in EXACT_CASES:
        for method in METHODS:
            pair = [row for row in rows if row["case"] == name and row["method"] == method]
            for metric in ("bks_rate", "near_bks_rate", "feasible_rate", "quality_mass"):
                max_ordering_error = max(
                    max_ordering_error,
                    abs(pair[0]["metrics"][metric] - pair[1]["metrics"][metric]),
                )
    if max_ordering_error > 1e-10:
        raise AssertionError(f"Exact ordering remap error: {max_ordering_error}")
    payload = {
        "stage": "external_exact_statevector",
        "complete": True,
        "provenance": provenance(),
        "max_ordering_error": max_ordering_error,
        "rows": rows,
    }
    write_json(path, payload)
    return payload


def job_identity(row: dict) -> tuple:
    return (
        row["case"],
        row["method"],
        row["ordering"],
        row["setting"],
        int(row["seed"]),
    )


def run_mps_cohort(
    path: Path,
    stage: str,
    cases: dict[str, int],
    methods: tuple[str, ...],
    seeds: tuple[int, ...],
    shots: int,
) -> dict:
    checkpoint = read_json(path) if path.exists() else {}
    rows = checkpoint.get("rows", [])
    unique = {job_identity(row): row for row in rows}
    errors = checkpoint.get("errors", [])
    for name, cap in cases.items():
        case_cache = {
            ordering: rr.prepare_case(name, cap, ordering)
            for ordering in ("sorted", "spectral")
        }
        for method in methods:
            genome = METHODS[method]
            for ordering, case in case_cache.items():
                for setting_name, setting in SETTINGS.items():
                    for seed in seeds:
                        key = (name, method, ordering, setting_name, seed)
                        if key in unique:
                            continue
                        try:
                            result = rr.mps_evaluate(
                                case,
                                np.asarray(genome),
                                DEPTH,
                                shots,
                                seed,
                                setting["bond"],
                                setting["cutoff"],
                            )
                        except Exception as exc:
                            errors.append(
                                {
                                    "identity": list(key),
                                    "type": type(exc).__name__,
                                    "message": str(exc),
                                }
                            )
                            write_json(
                                path,
                                {
                                    "stage": stage,
                                    "complete": False,
                                    "protocol_sha256": sha256(PROTOCOL),
                                    "rows": list(unique.values()),
                                    "errors": errors,
                                },
                            )
                            raise
                        row = {
                            "case": name,
                            "bks": BKS[name],
                            "max_degree": cap,
                            "qubits": case.qubits,
                            "method": method,
                            "genome": genome,
                            "depth": DEPTH,
                            "ordering": ordering,
                            "setting": setting_name,
                            "bond": setting["bond"],
                            "cutoff": setting["cutoff"],
                            "seed": seed,
                            "shots": shots,
                            **result,
                        }
                        unique[key] = row
                        write_json(
                            path,
                            {
                                "stage": stage,
                                "complete": False,
                                "protocol_sha256": sha256(PROTOCOL),
                                "rows": list(unique.values()),
                                "errors": errors,
                            },
                        )
    rows = sorted(unique.values(), key=job_identity)
    expected = len(cases) * len(methods) * 2 * len(SETTINGS) * len(seeds)
    if len(rows) != expected:
        raise AssertionError(f"{stage}: expected {expected} jobs, found {len(rows)}")
    payload = {
        "stage": stage,
        "complete": True,
        "provenance": provenance(),
        "cases": cases,
        "methods": methods,
        "settings": SETTINGS,
        "seeds": seeds,
        "shots_per_job": shots,
        "expected_jobs": expected,
        "rows": rows,
        "errors": errors,
    }
    write_json(path, payload)
    return payload


def stage_core() -> dict:
    return run_mps_cohort(
        RESULTS / "core_mps.json",
        "external_core_mps",
        CORE_CASES,
        tuple(METHODS),
        CORE_SEEDS,
        CORE_SHOTS,
    )


def stage_scale() -> dict:
    return run_mps_cohort(
        RESULTS / "scale_mps.json",
        "external_scale_mps",
        SCALE_CASES,
        ("published_lr", "prior_matched_random"),
        SCALE_SEEDS,
        SCALE_SHOTS,
    )


def aggregate(rows: list[dict]) -> list[dict]:
    groups = {}
    for row in rows:
        key = (row["case"], row["method"], row["ordering"], row["setting"])
        groups.setdefault(key, []).append(row)
    output = []
    for key, jobs in sorted(groups.items()):
        total = sum(job["metrics"]["total_shots"] for job in jobs)
        output.append(
            {
                "case": key[0],
                "method": key[1],
                "ordering": key[2],
                "setting": key[3],
                "jobs": len(jobs),
                "total_shots": total,
                "bks_rate": sum(job["metrics"]["bks_hits"] for job in jobs) / total,
                "near_bks_rate": sum(job["metrics"]["near_bks_hits"] for job in jobs) / total,
                "feasible_rate": sum(job["metrics"]["feasible_shots"] for job in jobs) / total,
                "median_elapsed_seconds": float(np.median([job["elapsed_seconds"] for job in jobs])),
                "resources": jobs[0]["resources"],
            }
        )
    return output


def paired_effect(rows: list[dict], candidate: str, setting: str) -> dict:
    selected = [row for row in rows if row["setting"] == setting]
    reference = {
        (row["case"], row["ordering"], row["seed"]): row
        for row in selected
        if row["method"] == "published_lr"
    }
    candidates = {
        (row["case"], row["ordering"], row["seed"]): row
        for row in selected
        if row["method"] == candidate
    }
    keys = sorted(set(reference) & set(candidates))
    result = {"candidate": candidate, "setting": setting, "paired_jobs": len(keys), "metrics": {}}
    for metric_index, metric in enumerate(("bks_rate", "near_bks_rate", "feasible_rate")):
        differences = np.asarray(
            [candidates[key]["metrics"][metric] - reference[key]["metrics"][metric] for key in keys]
        )
        rng = np.random.default_rng(47000 + metric_index)
        indices = rng.integers(0, len(differences), size=(BOOTSTRAP_DRAWS, len(differences)))
        means = differences[indices].mean(axis=1)
        observed = abs(float(differences.mean()))
        if len(differences) <= 20:
            signs = np.asarray(
                [[1.0 if (mask >> index) & 1 else -1.0 for index in range(len(differences))]
                 for mask in range(1 << len(differences))]
            )
        else:
            signs = rng.choice((-1.0, 1.0), size=(200_000, len(differences)))
        permutation_means = np.abs((signs * differences).mean(axis=1))
        result["metrics"][metric] = {
            "mean_difference": float(differences.mean()),
            "ci95": [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))],
            "wins": int(np.sum(differences > 0)),
            "ties": int(np.sum(differences == 0)),
            "losses": int(np.sum(differences < 0)),
            "sign_flip_p_two_sided": float(np.mean(permutation_means >= observed - 1e-15)),
        }
    return result


def stage_analyze() -> dict:
    exact = read_json(RESULTS / "exact_statevector.json") if (RESULTS / "exact_statevector.json").exists() else None
    datasets = []
    for name in ("core_mps.json", "scale_mps.json"):
        path = RESULTS / name
        if path.exists():
            datasets.append(read_json(path))
    rows = [row for dataset in datasets for row in dataset.get("rows", [])]
    completed = all(dataset.get("complete", False) for dataset in datasets) and len(datasets) == 2
    summary = aggregate(rows)
    effects = [
        paired_effect(rows, candidate, setting)
        for candidate in ("prior_evolutionary", "prior_matched_random")
        if any(row["method"] == candidate for row in rows)
        for setting in SETTINGS
    ]
    matched = {row["setting"]: row for row in effects if row["candidate"] == "prior_matched_random"}
    reversal = None
    if set(matched) == set(SETTINGS):
        released = matched["released"]["metrics"]["bks_rate"]["mean_difference"]
        confirm = matched["confirm"]["metrics"]["bks_rate"]["mean_difference"]
        reversal = bool(np.sign(released) != np.sign(confirm) and released != 0 and confirm != 0)
    payload = {
        "stage": "external_validity_analysis",
        "complete": completed,
        "protocol_sha256": sha256(PROTOCOL),
        "datasets": [dataset["stage"] for dataset in datasets],
        "exact_complete": bool(exact and exact.get("complete")),
        "summary": summary,
        "paired_effects": effects,
        "matched_bks_fidelity_reversal": reversal,
    }
    write_json(RESULTS / "analysis.json", payload)
    lines = [
        "# Cross-family external-validity report",
        "",
        f"- Completed MPS cohorts: `{completed}`.",
        f"- Completed exact audit: `{bool(exact and exact.get('complete'))}`.",
        f"- MPS jobs currently available: {len(rows)} / 408.",
        f"- Matched-schedule aggregate BKS fidelity reversal: `{reversal}`.",
        "",
        "## Aggregate paired effects versus published LR",
        "",
        "| Candidate | Setting | Metric | Difference | 95% CI | p |",
        "|---|---|---|---:|---:|---:|",
    ]
    for effect in effects:
        for metric, stats in effect["metrics"].items():
            lines.append(
                f"| {effect['candidate']} | {effect['setting']} | {metric} | "
                f"{stats['mean_difference']:+.5f} | [{stats['ci95'][0]:+.5f}, "
                f"{stats['ci95'][1]:+.5f}] | {stats['sign_flip_p_two_sided']:.6g} |"
            )
    lines.extend(
        [
            "",
            "Partial results are never interpreted as a completed cohort. Per-case and per-seed "
            "data remain in the checkpoint artifacts for independent re-analysis.",
        ]
    )
    (HERE / "EXTERNAL_VALIDITY_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=("certify", "exact", "core", "scale", "analyze", "all"),
        default="all",
    )
    args = parser.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    stages = {
        "certify": stage_certify,
        "exact": stage_exact,
        "core": stage_core,
        "scale": stage_scale,
        "analyze": stage_analyze,
    }
    selected = list(stages) if args.stage == "all" else [args.stage]
    for name in selected:
        start = perf_counter()
        print(f"[{name}] starting", flush=True)
        stages[name]()
        print(f"[{name}] complete in {perf_counter() - start:.3f}s", flush=True)


if __name__ == "__main__":
    main()
