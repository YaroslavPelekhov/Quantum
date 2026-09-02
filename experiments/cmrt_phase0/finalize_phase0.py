"""Build the CMRT human report, compact tables, legacy audit, and manifest."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from experiments.cmrt_phase0.legacy_ibm_archive import load_legacy_ibm_smoke_audit


REPO = Path(__file__).resolve().parents[2]
EXPERIMENT = REPO / "experiments" / "cmrt_phase0"
RESULTS = REPO / "results" / "cmrt_phase0"


def _load() -> tuple[dict[str, Any], dict[str, Any]]:
    protocol = json.loads((EXPERIMENT / "protocol.json").read_text(encoding="utf-8"))
    result = json.loads((RESULTS / "phase0_results.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256((EXPERIMENT / "protocol.json").read_bytes()).hexdigest()
    if result["protocol_sha256"] != digest:
        raise AssertionError("phase0 result does not match the frozen protocol")
    return protocol, result


def _write_method_summary(result: dict[str, Any]) -> None:
    path = RESULTS / "heldout_method_summary.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "method",
                "qhat",
                "accepted_rows",
                "total_rows",
                "accepted_fraction",
                "selective_accuracy",
                "covered_blocks",
                "total_blocks",
                "row_coverage",
                "median_interval_width",
            ]
        )
        for method, evaluation in sorted(result["evaluations"].items()):
            metrics = evaluation["metrics"]
            writer.writerow(
                [
                    method,
                    evaluation["qhat"],
                    metrics["n_certified"],
                    metrics["n_total"],
                    metrics["coverage"],
                    metrics["selective_accuracy"],
                    evaluation["covered_blocks"],
                    evaluation["total_test_blocks"],
                    evaluation["row_coverage"],
                    evaluation["median_interval_width"],
                ]
            )


def _write_heldout_rows(result: dict[str, Any]) -> None:
    path = RESULTS / "heldout_cmrt_rows.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "graph_id",
                "depth",
                "snapshot",
                "truth_gap",
                "center",
                "scale",
                "lower",
                "upper",
                "decision",
                "truth_sign",
                "covered",
            ],
        )
        writer.writeheader()
        for record in result["evaluations"]["cmrt"]["test_records"]:
            writer.writerow({key: record[key] for key in writer.fieldnames})


def _write_figure(result: dict[str, Any]) -> None:
    cmrt = result["evaluations"]["cmrt"]
    records = cmrt["test_records"]
    colors = {"primary_0": "#4477AA", "primary_1": "#EE6677", "primary_2": "#228833"}
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4), constrained_layout=True)
    for snapshot, color in colors.items():
        selected = [row for row in records if row["snapshot"] == snapshot]
        axes[0].scatter(
            [max(row["scale"] - 1e-4, 1e-12) for row in selected],
            [max(abs(row["truth_gap"] - row["center"]), 1e-12) for row in selected],
            s=24,
            alpha=0.75,
            label=snapshot,
            color=color,
        )
    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("metamorphic simulator spread")
    axes[0].set_ylabel("absolute hardware-surrogate residual")
    axes[0].set_title(f"Correlation exists (Spearman={result['decision']['spread_residual_spearman']:.3f})")
    axes[0].legend(frameon=False, fontsize=8)

    order = [
        "cmrt",
        "unscaled_ensemble",
        "gate_proxy",
        "single_high_bond",
        "exact_noiseless",
        "nominal_noise",
    ]
    x = list(range(len(order)))
    coverage = [result["evaluations"][name]["metrics"]["coverage"] for name in order]
    accuracy = [
        result["evaluations"][name]["metrics"]["selective_accuracy"] or 0.0 for name in order
    ]
    width = 0.38
    axes[1].bar([value - width / 2 for value in x], coverage, width, label="accepted fraction", color="#4477AA")
    axes[1].bar([value + width / 2 for value in x], accuracy, width, label="selective accuracy", color="#CC6677")
    axes[1].axhline(0.5, color="black", linestyle="--", linewidth=0.8, label="50% coverage gate")
    axes[1].set_xticks(x, [name.replace("_", "\n") for name in order], fontsize=7)
    axes[1].set_ylim(0.0, 1.05)
    axes[1].set_ylabel("fraction")
    axes[1].set_title("CMRT is accurate only by abstaining too often")
    axes[1].legend(frameon=False, fontsize=8, loc="lower right")
    fig.savefig(RESULTS / "cmrt_diagnostics.png", dpi=200)
    plt.close(fig)


def _format_metric(value: float | None, digits: int = 3) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def _write_report(protocol: dict[str, Any], result: dict[str, Any], legacy: dict[str, Any]) -> None:
    decision = result["decision"]
    cmrt = result["evaluations"]["cmrt"]
    metrics = cmrt["metrics"]
    shift = result["shift_evaluation"]["metrics"]
    shot = result["shot_audit"]
    rows = result["rows"]
    probabilities = [
        value
        for row in rows
        for value in (
            abs(float(row["schedule_selection"]["p_a_exact"])),
            abs(float(row["schedule_selection"]["p_b_exact"])),
        )
    ]
    ideal_gaps = [abs(float(row["exact_noiseless_gap"])) for row in rows]
    median_ideal_gap = statistics.median(ideal_gaps)
    test_sizes: dict[int, int] = {}
    for graph in result["cohort"]["graphs"]:
        if graph["split"] == "test":
            test_sizes[int(graph["n_qubits"])] = test_sizes.get(int(graph["n_qubits"]), 0) + 1
    failed = ", ".join(decision["failed_gates"])
    method_lines = []
    for method, evaluation in sorted(result["evaluations"].items()):
        item = evaluation["metrics"]
        method_lines.append(
            f"| `{method}` | {item['n_certified']}/{item['n_total']} "
            f"({item['coverage']:.1%}) | {_format_metric(item['selective_accuracy'])} | "
            f"{evaluation['covered_blocks']}/{evaluation['total_test_blocks']} | "
            f"{evaluation['median_interval_width']:.6g} |"
        )
    gate_lines = []
    for name, check in decision["checks"].items():
        gate_lines.append(f"| `{name}` | {'PASS' if check['pass'] else 'FAIL'} |")
    legacy_blocks = legacy["blocks"]
    report = f"""# CMRT offline Phase-0 final report

## Verdict

**{decision['terminal_label']}**.  The candidate passes {decision['passed_gate_count']} of
{decision['total_gate_count']} frozen gates.  It is not authorized for QPU spending and it
does not support an A* claim.

The potentially interesting part is real: approximate representation spread is
strongly associated with the simulator-to-noise-surrogate residual on the held-out
rows (descriptive Spearman **{decision['spread_residual_spearman']:.3f}**).  Rows are
clustered within 12 graphs and spread repeats across noise snapshots, so this point
estimate is not an independent-sample significance claim.  The association does
not become a useful selective decision rule.  CMRT accepts only
**{metrics['n_certified']}/{metrics['n_total']} ({metrics['coverage']:.1%})** rows,
below the frozen 50% gate, even though those accepted signs are all correct.  Only
**{cmrt['covered_blocks']}/{cmrt['total_test_blocks']}** held-out graph blocks receive
simultaneous interval coverage, below the required 11/12.

Six binding gates fail: {failed}.

## What was tested

- 36 connected, non-isomorphic, maximum-degree-three MIS graphs at 8--13 qubits;
- whole-graph split: 24 calibration and 12 held out;
- depths 2, 3, and 4;
- six approximate simulators per schedule: TT bond caps 2/4/8 crossed with
  natural and degree/BFS qubit orders;
- three primary coherent/readout/depolarizing noise surrogates plus one stronger
  shifted surrogate;
- a graph-block maximum nonconformity score, so all depths and primary snapshots
  are covered jointly rather than treated as independent rows.

The exact-equivalence audit has maximum probability-gap discrepancy
`{result['audit']['maximum_exact_equivalence_gap_error']:.3e}` across
{result['audit']['equivalence_checks']} checks.  The full frozen run took
{result['audit']['runtime_seconds']:.1f} seconds.

## Held-out comparison

| method | accepted signs | selective accuracy | covered graph blocks | median interval width |
|---|---:|---:|---:|---:|
{chr(10).join(method_lines)}

At CMRT's accepted count, both exact-noiseless and nominal-noise baselines have
zero sign error as well, so CMRT's frozen relative error reduction is **0%**, not
the required 25%.  CMRT beats the unscaled and gate-proxy rules only on a smaller
common subset; that does not satisfy the all-baseline claim.

## Binding gates

| gate | outcome |
|---|---:|
{chr(10).join(gate_lines)}

On the deliberately shifted snapshot, CMRT keeps 25.0% coverage but its accepted
sign accuracy falls to **{_format_metric(shift['selective_accuracy'])}**, below the
0.80 gate.  This is direct evidence that the calibrated abstention rule is not
robust to the device shift represented by the stress test.

## Schedule and measurement feasibility

Every one of the {len(rows)} graph-depth rows used the preregistered fallback.
Exact event probabilities lie between `{min(probabilities):.3e}` and
`{max(probabilities):.3e}`; the median absolute ideal schedule gap is only
`{median_ideal_gap:.3e}`.  A hardware ranking study built
from these schedules would therefore be shot-starved rather than merely
miscalibrated.  In the separate 4,096-shot audit, Bonferroni-adjusted descriptive
intervals resolve only **{shot['resolved_contrasts']}/{shot['total_contrasts']}**
contrasts ({shot['resolved_fraction']:.1%}).

This failure is terminal under the frozen protocol.  Retuning schedules, widening
the event, or lowering the coverage gate after seeing the probabilities would be
a new post-hoc experiment and cannot rescue CMRT.

## Split limitation

The frozen global hash split is leakage-free but poorly stratified:
`{json.dumps(test_sizes, sort_keys=True)}` held-out graphs by size.  It includes no
`n=9` or `n=13` graphs.  The split was not changed after this was discovered;
its limited external validity is another reason not to escalate.

## Real IBM archive smoke audit

The read-only loader recovered two distinct `ibm_boston` jobs from the local
submodule object database:

- `{legacy_blocks[0]['job_id']}`: lambda={legacy_blocks[0]['lambda_penalty']},
  {legacy_blocks[0]['total_raw_feasible_shots']}/{legacy_blocks[0]['total_shots']}
  raw feasible shots;
- `{legacy_blocks[1]['job_id']}`: lambda={legacy_blocks[1]['lambda_penalty']},
  {legacy_blocks[1]['total_raw_feasible_shots']}/{legacy_blocks[1]['total_shots']}
  raw feasible shots.

These are two jobs but only one graph and one backend; lambda changes between
them, and transpiled circuits and calibration snapshots are missing.  Their 190
within-job pairs are correlated.  They validate ingestion and provenance only;
they cannot calibrate or test conformal transfer.

## Research interpretation

The negative result is sharper than “we need more data.”  In a noiseless-outcome
offline setting deliberately favorable to detecting the mechanism, representation
spread correlates with residual size but fails to deliver the registered coverage,
matched-baseline advantage, shifted robustness, or shot feasibility.  Therefore
the conjunction does not justify real-server spending.

The broad neighboring space is also occupied by hardware circuit ranking,
capability models, device-transfer noise models, metamorphic quantum testing, and
conformal/selective prediction.  The correct action is to retain CMRT as a
falsified candidate and not rename it into another uncertainty or ranking claim.

## Reproduction

```powershell
python -m pytest experiments/cmrt_phase0 -q
python -m experiments.cmrt_phase0.run_phase0
python -m experiments.cmrt_phase0.finalize_phase0
```

No QPU job is submitted by any command above.
"""
    (RESULTS / "FINAL_REPORT.md").write_text(report, encoding="utf-8")


def _write_manifest() -> None:
    files: list[Path] = []
    for root in (EXPERIMENT, RESULTS):
        files.extend(
            path
            for path in root.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.name != "MANIFEST.json"
        )
    hashes = {
        path.relative_to(REPO).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(files)
    }
    manifest = {
        "experiment": "conformal_metamorphic_rank_transfer_phase0",
        "terminal_label": "KILL_CMRT_AS_ASTAR_SOURCE",
        "qpu_jobs_submitted": 0,
        "files": hashes,
    }
    (RESULTS / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )


def main() -> None:
    protocol, result = _load()
    RESULTS.mkdir(parents=True, exist_ok=True)
    legacy = load_legacy_ibm_smoke_audit(REPO).to_dict()
    (RESULTS / "legacy_ibm_smoke.json").write_text(
        json.dumps(legacy, indent=2, sort_keys=True), encoding="utf-8"
    )
    _write_method_summary(result)
    _write_heldout_rows(result)
    _write_figure(result)
    _write_report(protocol, result, legacy)
    _write_manifest()
    print(RESULTS / "FINAL_REPORT.md")


if __name__ == "__main__":
    main()
