"""Discretization audit for the finite-horizon boundary-response rank."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.linalg import hankel, svdvals

from .run_phase0 import OUT, REGIMES, effective_rank, relative_tail, response_on_grid


HANKEL_SIZES = (128, 256, 512)
HORIZONS = (5.0, 10.0, 20.0)
TARGET_K = 13


def main() -> None:
    rows: list[dict[str, object]] = []
    for regime in REGIMES:
        for horizon in HORIZONS:
            registered_rank = None
            for size in HANKEL_SIZES:
                response = response_on_grid(TARGET_K, horizon, regime, 2 * size - 1)
                matrix = hankel(response[:size], response[size - 1 :])
                values = svdvals(matrix)
                rank_1pct = effective_rank(values, 0.01)
                if size == 256:
                    registered_rank = rank_1pct
                rows.append(
                    {
                        "k": TARGET_K,
                        "horizon": horizon,
                        "regime": regime,
                        "hankel_size": size,
                        "sample_count": 2 * size - 1,
                        "response_zero_error": abs(response[0] - 1.0),
                        "effective_rank_1pct": rank_1pct,
                        "effective_rank_1e-6": effective_rank(values, 1e-6),
                        "rank64_relative_residual": relative_tail(values, 64),
                        "leading_singular_values_normalized": json.dumps(
                            (values[:12] / values[0]).tolist()
                        ),
                    }
                )
            final = rows[-1]
            final["registered_rank_256"] = registered_rank
            final["size512_rank_delta"] = abs(int(final["effective_rank_1pct"]) - int(registered_rank))
            final["case_passes"] = (
                int(final["size512_rank_delta"]) <= 1
                and float(final["rank64_relative_residual"]) < 1e-8
                and float(final["response_zero_error"]) < 1e-10
            )

    final_rows = [row for row in rows if row["hankel_size"] == 512]
    summary = {
        "all_cases_pass": all(bool(row["case_passes"]) for row in final_rows),
        "cases": final_rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "rank_grid_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = sorted({key for row in rows for key in row})
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "rank_grid_audit_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

