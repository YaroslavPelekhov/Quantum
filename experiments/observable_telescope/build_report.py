"""Build the combined 7q/18q observable-telescope research report."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "observable_telescope"


def read_json(name: str):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    summary = read_json("summary.json")
    runs = [
        read_json("ibm32_released_sorted.json"),
        read_json("ibm32_confirm_sorted.json"),
        read_json("ibm32_cutoff1e-5_sorted.json"),
    ]
    case_lines = "\n".join(
        f"| {case} | {stats['certified']} / {stats['total']} |"
        for case, stats in summary["per_case"].items()
    )
    setting_lines = []
    for payload in runs:
        pair = payload["pair"]
        rows = payload["rows"]
        setting_lines.append(
            f"| {pair['setting']} | {rows[0]['bond']} | {rows[0]['cutoff']:.0e} | "
            f"{pair['mps_delta']:.6f} | {pair['observable_telescope_pair_width']:.6f} | "
            f"{'yes' if pair['certified'] else 'no'} | "
            f"{sum(row['prefix_replay_seconds'] for row in rows):.1f} | "
            f"{max(row['peak_block_environment_bytes'] for row in rows) / 2**20:.0f} |"
        )
    max_identity = max(
        row["telescope_identity_error"] for payload in runs for row in payload["rows"]
    )
    max_regression = max(
        row["frozen_rankcert_regression_error"] for payload in runs for row in payload["rows"]
    )
    report = f"""# Observable-Telescope RankCert: research pilot

## Main result

The observable-aware exact-backward verifier materially improves the rigorous
RankCert coverage on the frozen QOBLIB-derived cohort.

- On the complete 7q matrix it certifies **{summary['telescope_certified']} / {summary['pair_rows']}** LR-vs-MR
  rankings, versus **{summary['accumulated_angle_certified_same_cohort']} / {summary['pair_rows']}** for accumulated-angle RankCert,
  with zero wrong certified signs.
- On the real 18q `ibm32` circuit, accumulated-angle RankCert is vacuous
  (pair width 2.0) for all tested settings. The new verifier certifies both
  `confirm` and `cutoff1e-5` on sorted ordering.
- The released low-resource point remains uncertified. This is the correct
  abstention: its new width is 0.524066 while the observed gap is 0.219681.

### Complete 7q matrix

| Case | Observable-telescope certified |
|---|---:|
{case_lines}

The new method adds {summary['newly_certified_over_accumulated_angle']} strict decisions over the prior bound.
The maximum telescope-identity error is
{summary['maximum_telescope_identity_error']:.3e}; the maximum frozen-run
regression error is {summary['maximum_frozen_rankcert_regression_error']:.3e}.

### Targeted 18q resource ladder (`ibm32`, sorted)

| Setting | Max bond | Cutoff | MPS MR-LR gap | Pair bound | Certified | Prefix replay, LR+MR (s) | Peak block environments (MiB) |
|---|---:|---:|---:|---:|:---:|---:|---:|
{chr(10).join(setting_lines)}

The exact gap is -0.246123 for all three rows. `confirm` is the practically
important point: bond 128 and cutoff 1e-4 already preserve the certified
method ranking. The stricter bond-1024 `cutoff1e-5` point narrows the pair bound
further to 0.008709 but costs substantially more replay time.

Across all 18q rows, the maximum telescope-identity error is {max_identity:.3e}
and the maximum difference from the frozen RankCert final BKS probability is
{max_regression:.3e}.

## Certificate construction

Let `Pi` be the BKS event projector and let `U_(t:T)` be the exact suffix after
checkpoint `t`. For the approximate MPS prefix state `phi_t`, define

`q_t = <phi_t | U_(t:T)^dagger Pi U_(t:T) | phi_t>`.

The first value is the exact BKS probability and the final value is the MPS BKS
probability. Hence

`p_MPS - p_exact = sum_t (q_t - q_(t-1))`

and the triangle inequality gives the rigorous trajectory-specific bound

`|p_MPS - p_exact| <= sum_t |q_t - q_(t-1)|`.

For an LR-vs-MR comparison, the two schedule bounds are added. A ranking is
certified only when the absolute approximate gap exceeds this paired width.

The BKS projector is low rank in this benchmark: rank 1 for chesapeake, rank 4
for football, and rank 2 for ibm32. On 18q, exact backward vectors are processed
in reverse blocks. Forward checkpoint states are obtained by independent
uninterrupted prefix replay from `|0>`; this avoids a verified Aer behavior in
which restarting from a saved MPS can change later SVD truncations.

## What is and is not claimed

This is a strict **a posteriori feasibility verifier**, not yet a scalable
internal MPS certificate. It uses exact backward suffix propagation with cost
exponential in qubit count. It does not infer rigor from Aer discarded weights,
and it does not claim performance on noisy hardware or finite-shot sampling.

The evidence consists of the full 40-trajectory 7q matrix plus three targeted
18q resource points on one ordering. The 18q result establishes scale transfer
for this frozen benchmark, but broader QOBLIB cases, orderings, and independent
circuits are still required for a main-paper generalization claim.

## Next research step

The paper-level algorithmic target is a scalable observable-aware verifier:
represent the backward BKS projector as a compressed MPO, propagate it through
the suffix, and attach a rigorous error budget to every MPO compression. The
exact-backward implementation here is the oracle against which that compressed
method should be calibrated. A successful method must retain the 18q
certificates above while bounding its own compression error and avoiding exact
`2^n` state vectors.
"""
    path = RESULTS / "REPORT.md"
    temporary = path.with_suffix(".md.tmp")
    temporary.write_text(report, encoding="utf-8", newline="\n")
    os.replace(temporary, path)

    import qiskit
    import qiskit_aer
    import numpy

    source_paths = [
        HERE / "run_observable_telescope.py",
        HERE / "run_observable_telescope_18q.py",
        HERE / "build_report.py",
        HERE / "test_observable_telescope.py",
        HERE / "README.md",
    ]
    artifact_paths = [
        RESULTS / "schedule_rows.json",
        RESULTS / "pair_rows.json",
        RESULTS / "summary.json",
        RESULTS / "ibm32_released_sorted.json",
        RESULTS / "ibm32_confirm_sorted.json",
        RESULTS / "ibm32_cutoff1e-5_sorted.json",
        RESULTS / "REPORT.md",
    ]
    manifest = {
        "stage": "observable_telescope_manifest",
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        "git_worktree_dirty_at_manifest_time": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=REPO, text=True
            ).strip()
        ),
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "qiskit": qiskit.__version__,
            "qiskit_aer": qiskit_aer.__version__,
            "numpy": numpy.__version__,
        },
        "sources": {
            str(item.relative_to(REPO)).replace("\\", "/"): {
                "bytes": item.stat().st_size, "sha256": sha256(item)
            } for item in source_paths
        },
        "artifacts": {
            str(item.relative_to(REPO)).replace("\\", "/"): {
                "bytes": item.stat().st_size, "sha256": sha256(item)
            } for item in artifact_paths
        },
    }
    manifest_path = RESULTS / "MANIFEST.json"
    manifest_temp = manifest_path.with_suffix(".json.tmp")
    manifest_temp.write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n",
        encoding="utf-8", newline="\n",
    )
    os.replace(manifest_temp, manifest_path)


if __name__ == "__main__":
    main()
