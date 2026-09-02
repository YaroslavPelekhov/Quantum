"""Audit the finite-n constants in the Haar/net QTV existence proof."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "results" / "aquila_gauge_resource_phase0"


def theorem_rows() -> list[dict]:
    rows = []
    for n in range(2, 13):
        vertices = 2**n
        edges = n * 2 ** (n - 1)
        increments = edges - 1
        log_union_bound = (vertices - 1) * math.log(87.0) - increments * math.log(4.0)
        rows.append(
            {
                "n": n,
                "vertices": vertices,
                "edges": edges,
                "spectral_increments": increments,
                "log_union_bound": log_union_bound,
                "existence_certified": log_union_bound < 0.0,
                "qtv_lower_coefficient_times_increments": math.pi / (8.0 * math.e),
                "time_lower_coefficient_rho_times_increments_over_width": 1.0
                / (4.0 * math.e),
            }
        )
    return rows


def main() -> None:
    rows = theorem_rows()
    with (OUTPUT / "theorem_union_bound.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    first_certified = next(row["n"] for row in rows if row["existence_certified"])
    payload = {
        "net_points_per_vertex_circle": 87,
        "net_radius_upper_rad": math.pi / 87.0,
        "required_net_radius_rad": math.pi / (32.0 * math.e),
        "first_n_certified": first_certified,
        "n6_log_union_bound": next(row["log_union_bound"] for row in rows if row["n"] == 6),
        "n7_log_union_bound": next(row["log_union_bound"] for row in rows if row["n"] == 7),
        "all_checks_pass": (
            math.pi / 87.0 < math.pi / (32.0 * math.e) and first_certified == 7
        ),
    }
    (OUTPUT / "theorem_audit.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2))
    if not payload["all_checks_pass"]:
        raise AssertionError("QTV theorem constant audit failed")


if __name__ == "__main__":
    main()
