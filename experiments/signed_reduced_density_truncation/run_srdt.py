"""Run frozen synthetic and real-data SRDT benchmarks."""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "signed_reduced_density_truncation"
sys.path[:0] = [str(HERE), str(REPO / "experiments" / "rankcert_mps")]

import rankcert_inputs
from srdt_core import atomic_json, cut_benchmark, sha256, synthetic_metrics


PROTOCOL = HERE / "PROTOCOL.md"
OUTPUT = RESULTS / "benchmark.json"
CASES = ("ibm32", "aves-sparrow-social")
ORDERINGS = ("sorted", "spectral")
RANKS = (2, 4, 8, 16, 32, 64)


def pair_specs(case: str, ordering: str) -> tuple[dict, dict]:
    rows = rankcert_inputs.load_specs()
    a = next(row for row in rows if (row["case"], row["ordering"], row["method"]) == (case, ordering, "published_lr"))
    b = next(row for row in rows if (row["case"], row["ordering"], row["method"]) == (case, ordering, "prior_matched_random"))
    return a, b


def main() -> None:
    payload = {
        "complete": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "protocol_sha256": sha256(PROTOCOL),
        "runner_sha256": sha256(Path(__file__)),
        "synthetic": [],
        "real": [],
    }
    for local_qubits in range(2, 9):
        row = synthetic_metrics(local_qubits)
        payload["synthetic"].append(row)
        print(
            f"[synthetic] n={row['total_qubits']} state_rank={row['state_a_required_schmidt_rank']} "
            f"contrast_rank={row['contrast_exact_rank']} ratio={row['state_to_contrast_rank_ratio']:.1f}x",
            flush=True,
        )
    atomic_json(OUTPUT, payload)

    for case in CASES:
        for ordering in ORDERINGS:
            spec_a, spec_b = pair_specs(case, ordering)
            state_a = np.asarray(np.load(spec_a["reference_file"], mmap_mode="r", allow_pickle=False))
            state_b = np.asarray(np.load(spec_b["reference_file"], mmap_mode="r", allow_pickle=False))
            sites = int(spec_a["qubits"])
            cohort = {
                "case": case,
                "ordering": ordering,
                "qubits": sites,
                "cuts": [],
            }
            for cut in sorted(set((3, 5, 7, min(9, sites // 2)))):
                result = cut_benchmark(state_a, state_b, cut, RANKS)
                cohort["cuts"].append(result)
                rank8 = next(row for row in result["rows"] if row["rank"] == 8)
                print(
                    f"[real] {case}/{ordering} cut={cut} "
                    f"signed_R8={rank8['signed_relative_error']:.4f} "
                    f"avg_R8={rank8['state_averaged_relative_error']:.4f}",
                    flush=True,
                )
            payload["real"].append(cohort)
            atomic_json(OUTPUT, payload)
    payload["complete"] = True
    atomic_json(OUTPUT, payload)
    print(json.dumps({"output": str(OUTPUT), "complete": True}, indent=2))


if __name__ == "__main__":
    main()
