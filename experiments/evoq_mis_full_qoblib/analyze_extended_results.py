"""Combine QAOA, independent cuTensorNet, and classical baseline artifacts."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import run_cycle as rc
from scipy.stats import fisher_exact


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
CUTN = RESULTS / "cutensornet"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def shots_to_95(rate: float):
    if rate <= 0:
        return None
    if rate >= 1:
        return 1
    return math.ceil(math.log(0.05) / math.log(1.0 - rate))


def decoded_cutensornet_rows(case):
    manifest = load(CUTN / "export_manifest.json")
    rows = []
    for path in sorted(CUTN.glob("raw_es60fst02_*shots.json")):
        raw = load(path)
        ordering = raw.get("ordering", "sorted")
        for item in raw.get("rows", []):
            counts = item["counts"]
            if ordering != "sorted":
                manifest_row = next(
                    row
                    for row in manifest["rows"]
                    if row["case"] == raw["case"]
                    and row["method"] == item["method"]
                    and row["ordering"] == ordering
                )
                node_order = manifest_row["qubit_node_order"]
                position = {node: i for i, node in enumerate(node_order)}
                remapped = {}
                for bitstring, count in counts.items():
                    canonical = "".join(
                        bitstring[position[node]] for node in sorted(node_order)
                    )
                    remapped[canonical] = remapped.get(canonical, 0) + count
                counts = remapped
            metrics = rc.summarize_counts(case, counts)
            rows.append(
                {
                    "source": path.relative_to(HERE).as_posix(),
                    "backend": "NVIDIA cuTensorNet MPS",
                    "ordering": ordering,
                    "bond": raw.get("bond"),
                    "cutoff": raw.get("discarded_weight_cutoff"),
                    "shots": raw["shots"],
                    "method": item["method"],
                    "elapsed_seconds": item["elapsed_seconds"],
                    **{
                        key: metrics[key]
                        for key in (
                            "bks_hits",
                            "bks_rate",
                            "near_bks_hits",
                            "near_bks_rate",
                            "feasible_rate",
                            "quality_mass",
                            "best_size",
                        )
                    },
                }
            )
    return rows


def main():
    case = rc.prepare_case(rc.TEST_NAME)
    classical = load(RESULTS / "classical_baselines.json")
    blind = load(RESULTS / "blind_test.json")
    analysis = load(RESULTS / "analysis_summary.json")
    cutn_rows = decoded_cutensornet_rows(case)

    batch_by_replicate = {}
    for row in blind["rows"]:
        batch_by_replicate[row["replicate"]] = row["elapsed_batch_seconds"]
    qaoa_allocated_seconds = sum(batch_by_replicate.values()) / 3.0
    qaoa_best = next(
        row
        for row in analysis["blind_summary"]
        if row["method"] == "matched_random_search"
    )
    full = classical["full_graph_heuristic"]
    kernel = classical["reduced_graph_heuristic"]
    exact = classical["exact"]
    independent_comparisons = []
    for cutoff in (1e-3, 1e-4):
        selected = [
            row
            for row in cutn_rows
            if row["ordering"] == "spectral"
            and row["bond"] == 128
            and row["cutoff"] == cutoff
            and row["shots"] == 5_000
        ]
        if len(selected) != 2:
            continue
        lr = next(row for row in selected if row["method"] == "published_lr")
        nonlinear = next(
            row for row in selected if row["method"] == "matched_random_search"
        )
        difference = nonlinear["bks_rate"] - lr["bks_rate"]
        standard_error = math.sqrt(
            nonlinear["bks_rate"] * (1 - nonlinear["bks_rate"]) / nonlinear["shots"]
            + lr["bks_rate"] * (1 - lr["bks_rate"]) / lr["shots"]
        )
        independent_comparisons.append(
            {
                "ordering": "spectral",
                "bond": 128,
                "cutoff": cutoff,
                "shots_per_method": 5_000,
                "lr_bks_hits": lr["bks_hits"],
                "nonlinear_bks_hits": nonlinear["bks_hits"],
                "lr_bks_rate": lr["bks_rate"],
                "nonlinear_bks_rate": nonlinear["bks_rate"],
                "nonlinear_minus_lr": difference,
                "normal_95_ci": [
                    difference - 1.96 * standard_error,
                    difference + 1.96 * standard_error,
                ],
                "two_sided_fisher_exact_p": float(
                    fisher_exact(
                        [
                            [nonlinear["bks_hits"], 5_000 - nonlinear["bks_hits"]],
                            [lr["bks_hits"], 5_000 - lr["bks_hits"]],
                        ]
                    ).pvalue
                ),
                "lr_near_bks_rate": lr["near_bks_rate"],
                "nonlinear_near_bks_rate": nonlinear["near_bks_rate"],
                "lr_feasible_rate": lr["feasible_rate"],
                "nonlinear_feasible_rate": nonlinear["feasible_rate"],
            }
        )
    comparison = {
        "qaoa_best": {
            **qaoa_best,
            "allocated_wall_seconds": qaoa_allocated_seconds,
        },
        "highs_exact": exact,
        "full_graph_greedy": {
            **full["summary"],
            "elapsed_seconds": full["elapsed_seconds"],
            "shots_to_95pct_bks": shots_to_95(full["summary"]["bks_rate"]),
            "bks_rate_ratio_to_qaoa": full["summary"]["bks_rate"]
            / qaoa_best["bks_rate"],
            "speedup_vs_qaoa_allocated_walltime": qaoa_allocated_seconds
            / full["elapsed_seconds"],
        },
        "qoblib_kernel_greedy": {
            **kernel["summary"],
            "elapsed_seconds": kernel["elapsed_seconds"],
            "shots_to_95pct_bks": shots_to_95(kernel["summary"]["bks_rate"]),
            "bks_rate_ratio_to_qaoa": kernel["summary"]["bks_rate"]
            / qaoa_best["bks_rate"],
            "speedup_vs_qaoa_allocated_walltime": qaoa_allocated_seconds
            / kernel["elapsed_seconds"],
        },
        "highs_speedup_vs_qaoa_allocated_walltime": qaoa_allocated_seconds
        / exact["elapsed_seconds"],
    }
    payload = {
        "stage": "extended_backend_and_classical_comparison",
        "case": rc.case_metadata(case),
        "comparison": comparison,
        "cutensornet_rows": cutn_rows,
        "cutensornet_5000shot_comparisons": independent_comparisons,
    }
    rc.write_json(RESULTS / "extended_comparison.json", payload)

    if cutn_rows:
        with (RESULTS / "cutensornet_sweep.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=list(cutn_rows[0]))
            writer.writeheader()
            writer.writerows(cutn_rows)

    report = f"""# Extended independent-backend and classical comparison

## Classical position

- HiGHS proves BKS {exact['objective_size']} with zero MIP gap in
  {exact['elapsed_seconds']:.6f} seconds.
- Randomized minimum residual degree on the full 186-vertex graph obtains
  {full['summary']['bks_hits']:,} BKS solutions in 15,000 starts
  ({full['summary']['bks_rate']:.3%}) in {full['elapsed_seconds']:.3f} seconds.
- The same heuristic on the released 55-variable QOBLIB kernel obtains
  {kernel['summary']['bks_hits']:,} BKS solutions
  ({kernel['summary']['bks_rate']:.3%}) in {kernel['elapsed_seconds']:.3f} seconds.
- The best QAOA schedule obtains {qaoa_best['bks_hits']} BKS samples
  ({qaoa_best['bks_rate']:.3%}) in 15,000 shots. One-third of the measured
  three-method batch wall time is {qaoa_allocated_seconds:.3f} seconds.

Thus full-graph greedy has {comparison['full_graph_greedy']['bks_rate_ratio_to_qaoa']:.1f}x
the BKS rate and is {comparison['full_graph_greedy']['speedup_vs_qaoa_allocated_walltime']:.1f}x
faster by allocated wall time. Kernel greedy has
{comparison['qoblib_kernel_greedy']['bks_rate_ratio_to_qaoa']:.1f}x the BKS rate
and is {comparison['qoblib_kernel_greedy']['speedup_vs_qaoa_allocated_walltime']:.1f}x faster.
These are classical dominance results, not quantum advantage results.

## Independent backend

The machine-readable cuTensorNet sweep is `results/cutensornet_sweep.csv`.
Small 12/15-qubit exact contractions match Qiskit statevectors at unit fidelity.
The 55-qubit exact contraction sampler returned an internal backend error after
293 seconds. Completed 55-qubit results therefore use the independent
cuTensorNet MPS implementation and are explicitly labeled approximate.

At spectral ordering, bond 128, and 5,000 shots per method, cutoff `1e-3`
produces 15 nonlinear versus 6 LR BKS hits (two-sided Fisher p=0.0780). At
cutoff `1e-4`, the counts are 11 versus 12 (p=1.0). Thus the independent backend
supports loss of the BKS advantage as accuracy is tightened, while it does not
establish a significant advantage for either schedule at the tighter point.
"""
    (HERE / "EXTENDED_BASELINE_REPORT.md").write_text(report, encoding="utf-8")
    print(
        f"full greedy/QAOA BKS ratio={comparison['full_graph_greedy']['bks_rate_ratio_to_qaoa']:.2f}; "
        f"kernel ratio={comparison['qoblib_kernel_greedy']['bks_rate_ratio_to_qaoa']:.2f}; "
        f"cuTensorNet rows={len(cutn_rows)}"
    )


if __name__ == "__main__":
    main()
