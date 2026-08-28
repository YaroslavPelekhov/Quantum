"""Build the frozen sparse-MPS DCS-RDT negative protocol report."""

from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "sparse_mps_dcsrdt"
sys.path.insert(0, str(REPO / "experiments" / "contrastive_tensor_simulation"))

from contrastive_core import atomic_json, sha256


def main() -> None:
    development_path = RESULTS / "development.json"
    development = json.loads(development_path.read_text(encoding="utf-8"))
    if not development.get("complete"):
        raise AssertionError("Incomplete development artifact")
    if development.get("success") or development.get("passed_rows") != 0:
        raise AssertionError("Unexpected sparse-MPS development verdict")
    if (RESULTS / "transfer.json").exists():
        raise AssertionError("Large transfer must not run after development failure")
    replication_path = RESULTS / "calibrated_replication.json"
    replication = json.loads(replication_path.read_text(encoding="utf-8"))
    if not replication.get("complete") or replication.get("success"):
        raise AssertionError("Unexpected calibrated replication verdict")
    if replication.get("passed_rows") != 0:
        raise AssertionError("Unexpected calibrated replication passes")
    semantics_path = RESULTS / "snapshot_semantics.json"
    semantics = json.loads(semantics_path.read_text(encoding="utf-8"))
    if not semantics.get("complete"):
        raise AssertionError("Incomplete snapshot semantics audit")
    rows = development["rows"]
    same_representation = [row["same_mps_representation_error"] for row in rows]
    backend_difference = [row["dense_operator_frobenius_error"] for row in rows]
    trace_difference = [abs(row["direct_mps_delta"] - row["exact_delta"]) for row in rows]

    lines = [
        "# Sparse-MPS DCS-RDT constructibility report",
        "",
        "## Verdict",
        "",
        "The frozen promotion protocol is **closed (0/4)**, so the 18/24-qubit",
        "large transfer stage was not run. The failure is caused by an over-tight",
        "cross-backend identity tolerance, not by the sparse-MPS contraction algebra.",
        "This distinction is diagnostic only and does not retroactively change the",
        "prespecified verdict.",
        "",
        "## Frozen development rows",
        "",
        "| case | ordering | direct gap | trace difference | operator difference | same-MPS identity | pass |",
        "|---|---|---:|---:|---:|---:|:---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['case']} | {row['ordering']} | {row['direct_mps_delta']:+.9f} | "
            f"{abs(row['direct_mps_delta'] - row['exact_delta']):.2e} | "
            f"{row['dense_operator_frobenius_error']:.2e} | "
            f"{row['same_mps_representation_error']:.2e} | no |"
        )
    lines.extend([
        "",
        "The protocol required `<1e-12` trace difference and `<1e-10` operator",
        "difference against the archived dense trajectory. Observed cross-backend",
        f"differences were `{min(trace_difference):.2e}`--`{max(trace_difference):.2e}`",
        f"and `{min(backend_difference):.2e}`--`{max(backend_difference):.2e}`.",
        "All runs had zero truncations, unit norm, and zero accumulated-angle error.",
        "",
        "When the dense operator is reconstructed from the *same returned MPS*,",
        f"the direct sparse contraction agrees within `{min(same_representation):.2e}`--",
        f"`{max(same_representation):.2e}`. This validates the implementation identity",
        "and locates the larger discrepancy in independent simulator trajectories.",
        "The repository's previously calibrated numerical simulation allowance is",
        "`1e-7`, but substituting it after observing this result would be retuning.",
        "",
        "## Algorithm retained from the kill test",
        "",
        "The implementation never requests a full statevector or `2^n` BKS mask.",
        "For the frozen unit-weight MIS scorers it enumerates the BKS support through",
        "independent-set backtracking, groups support strings by their right half,",
        "queries only the required MPS left slices, and accumulates the open",
        "decision-conditioned operator. The local spectral tail composes with",
        "RankCert as `epsilon_A+epsilon_B+tail+2e-7`.",
        "",
        "These properties are theorem/unit-test results, not evidence that the large",
        "benchmark passed. A future replication may freeze a same-trajectory identity",
        "test plus a separately calibrated backend-equivalence tolerance, but must be",
        "reported as a new protocol rather than a repair of this one.",
        "",
        "## Separately frozen calibrated replication",
        "",
        "After closing the primary result, a new protocol used the pre-existing",
        "RankCert `1e-7` numerical allowance and then opened the untouched 18/24-qubit",
        "cohort. It also failed `0/4`.",
        "",
        "| case | ordering | archive gap error | storage reduction | combined bound | pass |",
        "|---|---|---:|---:|---:|:---:|",
    ])
    for row in replication["rows"]:
        lines.append(
            f"| {row['case']} | {row['ordering']} | "
            f"{row['archived_gap_match_error']:.2e} | "
            f"{row['storage_reduction_factor']:.2f}x | "
            f"{row['combined_rank_bound']:.3f} | no |"
        )
    lines.extend([
        "",
        "All archived-gap discrepancies (`4.35e-4`--`1.30e-3`) exceed the calibrated",
        "tolerance. The inherited accumulated-angle bound saturates at `2.0` on every",
        "row, so no ideal-gap sign is certified. The 18-qubit rows save only",
        "6.83x--9.61x and miss the frozen 10x storage criterion; the 24-qubit rows",
        "save over 1500x but still fail reproducibility and certification.",
        "",
        "## Snapshot-semantics diagnosis",
        "",
        "On `ibm32/sorted`, a fresh `save_statevector` run reproduces the archived",
        "probabilities within `1.1e-15`, while `save_matrix_product_state` changes the",
        "two schedule probabilities by `8.01e-4` and `2.10e-3`. The resulting gap",
        f"changes by `{semantics['gap_difference']:.6f}`. Thus the large mismatch is",
        "specific to the terminal MPS snapshot/export path under truncation, not the",
        "sparse support contraction. Exported MPS tensors cannot be treated as",
        "semantically interchangeable with statevector readout from the same Aer MPS",
        "configuration without a separate calibration.",
        "",
    ])
    report = RESULTS / "REPORT.md"
    report.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    tracked = [
        HERE / "PROTOCOL.md",
        HERE / "CALIBRATED_REPLICATION_PROTOCOL.md",
        HERE / "sparse_mps_core.py",
        HERE / "run_sparse_mps.py",
        HERE / "run_calibrated_replication.py",
        HERE / "run_snapshot_semantics.py",
        HERE / "analyze_sparse_mps.py",
        HERE / "test_sparse_mps.py",
        HERE / "README.md",
        development_path,
        replication_path,
        semantics_path,
        report,
    ]
    manifest = {
        "complete": True,
        "development_success": False,
        "development_passed_rows": 0,
        "transfer_promoted": False,
        "calibrated_replication_success": False,
        "calibrated_replication_passed_rows": 0,
        "same_mps_identity_validated": max(same_representation) < 1e-12,
        "snapshot_path_gap_difference": semantics["gap_difference"],
        "files": {str(path.relative_to(REPO)): sha256(path) for path in tracked},
    }
    atomic_json(RESULTS / "manifest.json", manifest)
    print(json.dumps({
        "report": str(report),
        "development_passed": 0,
        "transfer_promoted": False,
        "calibrated_replication_passed": 0,
        "snapshot_gap_difference": semantics["gap_difference"],
        "same_mps_max_error": max(same_representation),
        "manifest_entries": len(tracked),
    }, indent=2))


if __name__ == "__main__":
    main()
