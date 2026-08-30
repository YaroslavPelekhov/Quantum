"""Post-hoc native-driver finite-time screen over every tested leaf reduction."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import networkx as nx

from qdk_core import HardBlockadeSystem, evolve_success


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "quantum_safe_kernelization_phase0"
SCREEN_STEPS = 120
CONFIRM_STEPS = 480
TIMES = (5.0, 10.0)


def reconstruct(code: str) -> nx.Graph:
    return nx.convert_node_labels_to_integers(nx.from_graph6_bytes(code.encode()), ordering="sorted")


def main() -> None:
    with (OUT / "leaf_reductions.csv").open(newline="", encoding="utf-8") as handle:
        reductions = list(csv.DictReader(handle))
    systems: dict[str, HardBlockadeSystem] = {}
    success: dict[tuple[str, float, int], float] = {}

    def evaluate(code: str, total_time: float, steps: int) -> float:
        key = (code, total_time, steps)
        if key not in success:
            if code not in systems:
                systems[code] = HardBlockadeSystem(reconstruct(code))
            success[key] = evolve_success(systems[code], total_time, 1.0, steps)
        return success[key]

    rows = []
    for index, reduction in enumerate(reductions):
        for total_time in TIMES:
            original = evaluate(reduction["graph6"], total_time, SCREEN_STEPS)
            reduced = evaluate(reduction["reduced_graph6"], total_time, SCREEN_STEPS)
            rows.append(
                {
                    "reduction_index": index,
                    "source": reduction["source"],
                    "graph6": reduction["graph6"],
                    "reduced_graph6": reduction["reduced_graph6"],
                    "n": int(reduction["n"]),
                    "leaf": int(reduction["leaf"]),
                    "neighbour": int(reduction["neighbour"]),
                    "coverage": float(reduction["lifted_optimum_coverage"]),
                    "total_time": total_time,
                    "screen_steps": SCREEN_STEPS,
                    "original_success": original,
                    "reduced_success": reduced,
                    "absolute_difference": abs(original - reduced),
                }
            )
        if (index + 1) % 100 == 0:
            print(f"screened {index + 1}/{len(reductions)} reductions", flush=True)

    rows.sort(key=lambda row: float(row["absolute_difference"]), reverse=True)
    confirmed = []
    for row in rows[:12]:
        original = evaluate(str(row["graph6"]), float(row["total_time"]), CONFIRM_STEPS)
        reduced = evaluate(str(row["reduced_graph6"]), float(row["total_time"]), CONFIRM_STEPS)
        confirmed.append(
            {
                **row,
                "confirm_steps": CONFIRM_STEPS,
                "confirmed_original_success": original,
                "confirmed_reduced_success": reduced,
                "confirmed_absolute_difference": abs(original - reduced),
            }
        )
    confirmed.sort(key=lambda row: float(row["confirmed_absolute_difference"]), reverse=True)

    with (OUT / "posthoc_broad_native_dynamics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (OUT / "posthoc_broad_native_dynamics_confirmed.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(confirmed[0]))
        writer.writeheader()
        writer.writerows(confirmed)

    report = {
        "screened_reductions": len(reductions),
        "screened_rows": len(rows),
        "native_driver": True,
        "screen_steps": SCREEN_STEPS,
        "confirm_steps": CONFIRM_STEPS,
        "times": TIMES,
        "screen_count_at_least_0p25": sum(float(row["absolute_difference"]) >= 0.25 for row in rows),
        "confirmed_count_at_least_0p25_among_top12": sum(
            float(row["confirmed_absolute_difference"]) >= 0.25 for row in confirmed
        ),
        "strongest_confirmed": confirmed[0],
        "strongest_endpoint_bijective_confirmed": max(
            (row for row in confirmed if float(row["coverage"]) == 1.0),
            key=lambda row: float(row["confirmed_absolute_difference"]),
            default=None,
        ),
    }
    (OUT / "broad_dynamics_summary.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
