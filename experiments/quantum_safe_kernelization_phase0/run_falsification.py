"""Post-hoc adversarial checks for apparent Phase-0 separations."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

import networkx as nx
import numpy as np

from qdk_core import (
    HardBlockadeSystem,
    evolve_success,
    gap_distortion,
    graph6,
    leaf_reduction,
    minimum_gap,
    minimum_gap_window,
    schedule,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "quantum_safe_kernelization_phase0"


def reconstruct(code: str) -> nx.Graph:
    return nx.convert_node_labels_to_integers(nx.from_graph6_bytes(code.encode()), ordering="sorted")


def load_rows() -> list[dict[str, str]]:
    with (OUT / "leaf_reductions.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def cutoff_scan(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    systems: dict[str, HardBlockadeSystem] = {}
    gaps: dict[str, tuple[float, float]] = {}

    def system(code: str) -> HardBlockadeSystem:
        if code not in systems:
            systems[code] = HardBlockadeSystem(reconstruct(code))
        return systems[code]

    def gap(code: str) -> tuple[float, float]:
        if code not in gaps:
            gaps[code] = minimum_gap_window(system(code), 0.10, 0.90, 1.0, 41)
        return gaps[code]

    output = []
    for row in rows:
        original_gap, original_s = gap(row["graph6"])
        reduced_gap, reduced_s = gap(row["reduced_graph6"])
        output.append(
            {
                "source": row["source"],
                "graph6": row["graph6"],
                "n": int(row["n"]),
                "leaf": int(row["leaf"]),
                "coverage": float(row["lifted_optimum_coverage"]),
                "original_gap_s_le_0p9": original_gap,
                "original_argmin_s": original_s,
                "reduced_gap_s_le_0p9": reduced_gap,
                "reduced_argmin_s": reduced_s,
                "cutoff_gap_distortion": gap_distortion(original_gap, reduced_gap),
                "preregistered_gap_distortion": float(row["native_gap_distortion"]),
            }
        )
    return output


def endpoint_scaling(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    selected = sorted(rows, key=lambda row: float(row["native_gap_distortion"]), reverse=True)[:12]
    output = []
    for rank, row in enumerate(selected):
        original = HardBlockadeSystem(reconstruct(row["graph6"]))
        reduced = HardBlockadeSystem(reconstruct(row["reduced_graph6"]))
        original_samples = []
        reduced_samples = []
        for epsilon in (0.08, 0.04, 0.02, 0.01, 0.005, 0.002):
            s = 1.0 - epsilon
            omega, delta = schedule(s)
            original_gap = original.gap(omega, delta)
            reduced_gap = reduced.gap(omega, delta)
            original_samples.append((epsilon, original_gap))
            reduced_samples.append((epsilon, reduced_gap))
            output.append(
                {
                    "rank": rank,
                    "graph6": row["graph6"],
                    "leaf": int(row["leaf"]),
                    "coverage": float(row["lifted_optimum_coverage"]),
                    "epsilon_from_endpoint": epsilon,
                    "omega": omega,
                    "original_gap": original_gap,
                    "reduced_gap": reduced_gap,
                    "gap_distortion": gap_distortion(original_gap, reduced_gap),
                }
            )
        x = np.log([sample[0] for sample in original_samples[-4:]])
        original_power = float(np.polyfit(x, np.log([sample[1] for sample in original_samples[-4:]]), 1)[0])
        reduced_power = float(np.polyfit(x, np.log([sample[1] for sample in reduced_samples[-4:]]), 1)[0])
        for record in output[-6:]:
            record["original_asymptotic_power"] = original_power
            record["reduced_asymptotic_power"] = reduced_power
    return output


def motif_baselines() -> list[dict[str, object]]:
    output = []
    for family in ("path", "star"):
        for n in range(3, 13):
            graph = nx.path_graph(n) if family == "path" else nx.star_graph(n - 1)
            reduction = leaf_reduction(graph, 0 if family == "path" else 1)
            original = HardBlockadeSystem(graph)
            reduced = HardBlockadeSystem(reduction.graph)
            original_full, original_full_s = minimum_gap(original)
            reduced_full, reduced_full_s = minimum_gap(reduced)
            original_cut, original_cut_s = minimum_gap_window(original, 0.1, 0.9, points=41)
            reduced_cut, reduced_cut_s = minimum_gap_window(reduced, 0.1, 0.9, points=41)
            original_success = evolve_success(original, 5.0, steps=480)
            reduced_success = evolve_success(reduced, 5.0, steps=480)
            output.append(
                {
                    "family": family,
                    "n": n,
                    "full_gap_distortion": gap_distortion(original_full, reduced_full),
                    "full_original_argmin_s": original_full_s,
                    "full_reduced_argmin_s": reduced_full_s,
                    "cutoff_gap_distortion": gap_distortion(original_cut, reduced_cut),
                    "cutoff_original_argmin_s": original_cut_s,
                    "cutoff_reduced_argmin_s": reduced_cut_s,
                    "T5_original_success": original_success,
                    "T5_reduced_success": reduced_success,
                    "T5_absolute_difference": abs(original_success - reduced_success),
                }
            )
    return output


def dynamics_convergence(summary: dict[str, object]) -> list[dict[str, object]]:
    candidate = summary["strongest_finite_time_difference"]
    graph = reconstruct(str(candidate["graph6"]))
    reduction = leaf_reduction(graph, int(candidate["leaf"]))
    original = HardBlockadeSystem(graph)
    reduced = HardBlockadeSystem(reduction.graph)
    output = []
    for steps in (120, 240, 480, 960):
        original_success = evolve_success(original, float(candidate["total_time"]), 1.0, steps)
        reduced_success = evolve_success(reduced, float(candidate["total_time"]), float(candidate["omega_scale"]), steps)
        output.append(
            {
                "steps": steps,
                "original_success": original_success,
                "reduced_success": reduced_success,
                "absolute_difference": abs(original_success - reduced_success),
            }
        )
    return output


def success_deletion_control(summary: dict[str, object]) -> dict[str, object]:
    candidate = summary["strongest_finite_time_difference"]
    graph = reconstruct(str(candidate["graph6"]))
    original = HardBlockadeSystem(graph)
    total_time = float(candidate["total_time"])
    selected_scale = float(candidate["omega_scale"])
    original_success = evolve_success(original, total_time, 1.0, 480)
    nodes = list(graph.nodes())
    records = []
    for scale in (1.0, selected_scale):
        differences = []
        leaf_difference = None
        for first_index, first in enumerate(nodes):
            for second in nodes[first_index + 1 :]:
                kept = [node for node in nodes if node not in (first, second)]
                reduced_graph = nx.convert_node_labels_to_integers(graph.subgraph(kept).copy(), ordering="sorted")
                reduced_success = evolve_success(HardBlockadeSystem(reduced_graph), total_time, scale, 480)
                difference = abs(original_success - reduced_success)
                differences.append(difference)
                if {first, second} == {int(candidate["leaf"]), int(candidate["neighbour"])}:
                    leaf_difference = difference
        assert leaf_difference is not None
        records.append(
            {
                "omega_scale": scale,
                "leaf_difference": leaf_difference,
                "deletion_median": float(np.median(differences)),
                "deletion_p90": float(np.quantile(differences, 0.9)),
                "deletion_max": float(np.max(differences)),
                "leaf_percentile": float(np.mean(np.asarray(differences) <= leaf_difference)),
            }
        )
    return {
        "graph6": candidate["graph6"],
        "n": candidate["n"],
        "total_time": total_time,
        "original_success": original_success,
        "records": records,
    }


def main() -> None:
    rows = load_rows()
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    cutoff = cutoff_scan(rows)
    endpoint = endpoint_scaling(rows)
    motifs = motif_baselines()
    convergence = dynamics_convergence(summary)
    success_control = success_deletion_control(summary)
    write_csv(OUT / "posthoc_cutoff_scan.csv", cutoff)
    write_csv(OUT / "posthoc_endpoint_scaling.csv", endpoint)
    write_csv(OUT / "posthoc_motif_baselines.csv", motifs)
    write_csv(OUT / "posthoc_dynamics_convergence.csv", convergence)

    strongest_cutoff = max(cutoff, key=lambda row: float(row["cutoff_gap_distortion"]))
    parsimonious = [row for row in cutoff if math.isclose(float(row["coverage"]), 1.0)]
    strongest_parsimonious = max(parsimonious, key=lambda row: float(row["cutoff_gap_distortion"]))
    endpoint_powers = Counter(round(float(row["original_asymptotic_power"])) for row in endpoint[::6])
    report = {
        "strongest_gap_after_removing_driver_rampdown": strongest_cutoff,
        "strongest_endpoint_bijective_gap_after_removing_driver_rampdown": strongest_parsimonious,
        "fivefold_cutoff_count": sum(float(row["cutoff_gap_distortion"]) >= 5.0 for row in cutoff),
        "fivefold_endpoint_bijective_cutoff_count": sum(
            float(row["cutoff_gap_distortion"]) >= 5.0 and math.isclose(float(row["coverage"]), 1.0) for row in cutoff
        ),
        "top_endpoint_original_gap_power_histogram": dict(endpoint_powers),
        "strongest_textbook_motif_gap_distortion": max(float(row["full_gap_distortion"]) for row in motifs),
        "strongest_textbook_motif_success_difference": max(float(row["T5_absolute_difference"]) for row in motifs),
        "dynamics_convergence": convergence,
        "strongest_success_same_size_deletion_control": success_control,
        "interpretation": (
            "The preregistered extreme is dominated by the final driver ramp-down and different perturbative "
            "splitting of classically degenerate optima.  Any surviving mid-schedule difference must still be "
            "judged against textbook motifs and generic same-size deletion."
        ),
    }
    (OUT / "falsification_summary.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
