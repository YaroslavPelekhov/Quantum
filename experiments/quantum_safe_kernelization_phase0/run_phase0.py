"""Run the preregistered dynamics-aware Rydberg MIS kernelization screen."""

from __future__ import annotations

import csv
import json
import math
import platform
import random
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import numpy as np

from qdk_core import (
    HardBlockadeSystem,
    driver_scales,
    evolve_success,
    gap_distortion,
    graph6,
    leaf_reduction,
    lifted_optimum_count,
    minimum_gap,
    relabel_graph,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "quantum_safe_kernelization_phase0"
SEED = 20260830
GAP_POINTS = 49
UDG_PER_SIZE = 24
TOP_PER_SOURCE = 6
DYNAMICS_TIMES = (5.0, 10.0, 20.0, 40.0)
DYNAMICS_STEPS = 240


class CachedPhysics:
    def __init__(self) -> None:
        self.systems: dict[str, HardBlockadeSystem] = {}
        self.gaps: dict[tuple[str, float], tuple[float, float]] = {}

    def system(self, graph: nx.Graph) -> HardBlockadeSystem:
        key = graph6(graph)
        if key not in self.systems:
            self.systems[key] = HardBlockadeSystem(graph)
        return self.systems[key]

    def minimum_gap(self, graph: nx.Graph, scale: float = 1.0) -> tuple[float, float]:
        key = (graph6(graph), round(scale, 12))
        if key not in self.gaps:
            self.gaps[key] = minimum_gap(self.system(graph), scale, GAP_POINTS)
        return self.gaps[key]


def atlas_graphs() -> list[nx.Graph]:
    graphs = []
    for raw in nx.graph_atlas_g():
        if 3 <= raw.number_of_nodes() <= 7 and nx.is_connected(raw) and any(degree == 1 for _, degree in raw.degree()):
            graphs.append(relabel_graph(raw))
    return graphs


def unit_disk_graphs() -> list[nx.Graph]:
    rng = random.Random(SEED)
    graphs: list[nx.Graph] = []
    seen: set[str] = set()
    for n in range(8, 13):
        accepted = 0
        attempts = 0
        while accepted < UDG_PER_SIZE and attempts < 50_000:
            attempts += 1
            radius = rng.uniform(0.24, 0.52)
            seed = rng.randrange(2**32)
            candidate = relabel_graph(nx.random_geometric_graph(n, radius, seed=seed))
            key = graph6(candidate)
            if key in seen or not nx.is_connected(candidate) or not any(degree == 1 for _, degree in candidate.degree()):
                continue
            seen.add(key)
            graphs.append(candidate)
            accepted += 1
        if accepted != UDG_PER_SIZE:
            raise RuntimeError(f"could only generate {accepted} UDG leaf instances at n={n}")
    return graphs


def reduction_rows(graphs: list[nx.Graph], source: str, physics: CachedPhysics) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for graph_index, graph in enumerate(graphs):
        original = physics.system(graph)
        original_gap, original_s = physics.minimum_gap(graph)
        for leaf in (node for node, degree in graph.degree() if degree == 1):
            reduction = leaf_reduction(graph, leaf)
            reduced = physics.system(reduction.graph)
            if original.alpha != reduced.alpha + 1:
                raise AssertionError("leaf rule failed exact MIS-value check")
            lifted_count, optimum_count = lifted_optimum_count(graph, reduction)
            scales = driver_scales(original.n, reduced.n)
            scale_records = []
            for scale in scales:
                reduced_gap, reduced_s = physics.minimum_gap(reduction.graph, scale)
                scale_records.append(
                    {
                        "omega_scale": scale,
                        "minimum_gap": reduced_gap,
                        "minimum_gap_s": reduced_s,
                        "gap_distortion": gap_distortion(original_gap, reduced_gap),
                    }
                )
            native = scale_records[0]
            rows.append(
                {
                    "source": source,
                    "graph_index": graph_index,
                    "graph6": graph6(graph),
                    "n": original.n,
                    "m": graph.number_of_edges(),
                    "leaf": leaf,
                    "neighbour": reduction.neighbour,
                    "neighbour_degree": graph.degree[reduction.neighbour],
                    "sibling_leaf_count": sum(graph.degree[w] == 1 for w in graph.neighbors(reduction.neighbour)),
                    "reduced_graph6": graph6(reduction.graph),
                    "reduced_n": reduced.n,
                    "reduced_m": reduction.graph.number_of_edges(),
                    "alpha": original.alpha,
                    "reduced_alpha_plus_offset": reduced.alpha + 1,
                    "optimum_count": optimum_count,
                    "lifted_optimum_count": lifted_count,
                    "lifted_optimum_coverage": lifted_count / optimum_count,
                    "endpoint_projector_obstruction": lifted_count < optimum_count,
                    "initial_projector_distance": 1.0,
                    "original_minimum_gap": original_gap,
                    "original_minimum_gap_s": original_s,
                    "reduced_minimum_gap": native["minimum_gap"],
                    "reduced_minimum_gap_s": native["minimum_gap_s"],
                    "native_gap_distortion": native["gap_distortion"],
                    "scale_controls": scale_records,
                }
            )
    return rows


def reconstruct_graph(code: str) -> nx.Graph:
    return relabel_graph(nx.from_graph6_bytes(code.encode()))


def top_candidates(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    selected = []
    for source in ("atlas", "unit_disk"):
        candidates = [row for row in rows if row["source"] == source]
        candidates.sort(key=lambda row: float(row["native_gap_distortion"]), reverse=True)
        selected.extend(candidates[:TOP_PER_SOURCE])
    return selected


def dynamics_rows(candidates: list[dict[str, object]], physics: CachedPhysics) -> list[dict[str, object]]:
    rows = []
    for rank, candidate in enumerate(candidates):
        graph = reconstruct_graph(str(candidate["graph6"]))
        reduction = leaf_reduction(graph, int(candidate["leaf"]))
        original = physics.system(graph)
        reduced = physics.system(reduction.graph)
        scales = driver_scales(original.n, reduced.n)
        for total_time in DYNAMICS_TIMES:
            original_success = evolve_success(original, total_time, 1.0, DYNAMICS_STEPS)
            for scale in scales:
                reduced_success = evolve_success(reduced, total_time, scale, DYNAMICS_STEPS)
                rows.append(
                    {
                        "candidate_rank": rank,
                        "source": candidate["source"],
                        "graph6": candidate["graph6"],
                        "n": candidate["n"],
                        "leaf": candidate["leaf"],
                        "neighbour": candidate["neighbour"],
                        "total_time": total_time,
                        "steps": DYNAMICS_STEPS,
                        "omega_scale": scale,
                        "original_success": original_success,
                        "reduced_success": reduced_success,
                        "absolute_success_difference": abs(original_success - reduced_success),
                    }
                )
    return rows


def deletion_controls(candidates: list[dict[str, object]], physics: CachedPhysics) -> list[dict[str, object]]:
    rows = []
    for rank, candidate in enumerate(candidates):
        graph = reconstruct_graph(str(candidate["graph6"]))
        original_gap = float(candidate["original_minimum_gap"])
        distortions = []
        nodes = list(graph.nodes())
        for first_index, first in enumerate(nodes):
            for second in nodes[first_index + 1 :]:
                kept = [node for node in nodes if node not in (first, second)]
                reduced = relabel_graph(graph.subgraph(kept).copy())
                reduced_gap, _ = physics.minimum_gap(reduced)
                distortions.append(gap_distortion(original_gap, reduced_gap))
        leaf_value = float(candidate["native_gap_distortion"])
        rows.append(
            {
                "candidate_rank": rank,
                "source": candidate["source"],
                "graph6": candidate["graph6"],
                "n": candidate["n"],
                "leaf": candidate["leaf"],
                "leaf_gap_distortion": leaf_value,
                "deletion_count": len(distortions),
                "deletion_median": float(np.median(distortions)),
                "deletion_p90": float(np.quantile(distortions, 0.9)),
                "deletion_max": float(np.max(distortions)),
                "leaf_percentile_among_deletions": float(np.mean(np.asarray(distortions) <= leaf_value)),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            cooked = {key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value for key, value in row.items()}
            writer.writerow(cooked)


def git_revision() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip() or "unknown"


def summarize(reductions, dynamics, controls, atlas_count, udg_count) -> dict[str, object]:
    strongest = max(reductions, key=lambda row: float(row["native_gap_distortion"]))
    strongest_dynamics = max(dynamics, key=lambda row: float(row["absolute_success_difference"]))
    robust_gap = []
    for row in reductions:
        if min(float(record["gap_distortion"]) for record in row["scale_controls"]) >= 5.0:
            robust_gap.append(row)
    strong_success = [row for row in dynamics if float(row["absolute_success_difference"]) >= 0.25]
    endpoint_failures = sum(bool(row["endpoint_projector_obstruction"]) for row in reductions)
    sibling_safe = [row for row in reductions if int(row["sibling_leaf_count"]) >= 2 and not row["endpoint_projector_obstruction"]]
    deletion_nontrivial = [row for row in controls if float(row["leaf_percentile_among_deletions"]) >= 0.9]
    criteria = {
        "strong_separation": bool(robust_gap or strong_success),
        "survives_driver_control": bool(robust_gap),
        "not_generic_same_size_deletion": bool(deletion_nontrivial),
        "nontrivial_whole_path_safe_rule": False,
        "prior_art_clear_for_narrow_claim": True,
    }
    criteria["phase0_survives"] = all(criteria.values())
    return {
        "frozen_configuration": {
            "seed": SEED,
            "gap_points": GAP_POINTS,
            "unit_disk_graphs_per_size": UDG_PER_SIZE,
            "top_candidates_per_source": TOP_PER_SOURCE,
            "dynamics_times": DYNAMICS_TIMES,
            "dynamics_steps": DYNAMICS_STEPS,
        },
        "counts": {
            "atlas_graphs": atlas_count,
            "unit_disk_graphs": udg_count,
            "oriented_leaf_reductions": len(reductions),
            "endpoint_projector_obstructions": endpoint_failures,
            "sibling_leaf_endpoint_bijections": len(sibling_safe),
        },
        "strongest_native_gap_distortion": strongest,
        "strongest_finite_time_difference": strongest_dynamics,
        "robust_fivefold_gap_count": len(robust_gap),
        "quarter_success_difference_count": len(strong_success),
        "top_deletion_control_pass_count": len(deletion_nontrivial),
        "criteria": criteria,
        "verdict": "CONTINUE" if criteria["phase0_survives"] else "KILL_NAIVE_WHOLE_PATH_FORMULATION",
        "structural_findings": {
            "forced_static_lift_initial_distance": 1.0,
            "reason": "negative-detuning initial ground state is empty, while the lift forces a selected leaf",
            "only_exhaustively_verified_endpoint_local_condition": "a neighbour with at least two leaf children makes those leaves persistent at the classical endpoint; it does not remove finite-Omega coupling",
            "nontrivial_whole_path_safe_rule_found": False,
        },
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    physics = CachedPhysics()
    atlas = atlas_graphs()
    unit_disk = unit_disk_graphs()
    unit_disk_records = []
    for index, graph in enumerate(unit_disk):
        unit_disk_records.append(
            {
                "index": index,
                "graph6": graph6(graph),
                "n": graph.number_of_nodes(),
                "edges": sorted([sorted(edge) for edge in graph.edges()]),
                "positions": {
                    str(node): [float(value) for value in graph.nodes[node]["pos"]]
                    for node in graph.nodes()
                },
            }
        )
    reductions = reduction_rows(atlas, "atlas", physics) + reduction_rows(unit_disk, "unit_disk", physics)
    candidates = top_candidates(reductions)
    dynamics = dynamics_rows(candidates, physics)
    controls = deletion_controls(candidates, physics)
    summary = summarize(reductions, dynamics, controls, len(atlas), len(unit_disk))
    metadata = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_revision_before_results": git_revision(),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "networkx": nx.__version__,
    }
    write_csv(OUT / "leaf_reductions.csv", reductions)
    write_csv(OUT / "finite_time_dynamics.csv", dynamics)
    write_csv(OUT / "same_size_deletion_controls.csv", controls)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (OUT / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    (OUT / "unit_disk_instances.json").write_text(
        json.dumps(unit_disk_records, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
