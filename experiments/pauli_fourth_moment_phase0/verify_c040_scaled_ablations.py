"""Independent standard-library verifier for frozen C040 results."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "results" / "pauli_fourth_moment_phase0" / "c040_scaled_ablations.json"
BASELINES = ("degree", "clique", "odd5", "odd7", "odd9")


def quantile(values, q):
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def check_summary(values, frozen):
    assert frozen["count"] == len(values)
    assert math.isclose(frozen["mean"], statistics.fmean(values), abs_tol=2e-12)
    assert math.isclose(frozen["median"], statistics.median(values), abs_tol=2e-12)
    assert math.isclose(frozen["p95"], quantile(values, 0.95), abs_tol=2e-12)
    assert math.isclose(frozen["max"], max(values), abs_tol=2e-12)
    exact = sum(value <= 1 + 1e-8 for value in values) / len(values)
    assert math.isclose(frozen["exact_fraction"], exact, abs_tol=2e-12)


def verify(report):
    assert report["experiment"] == "C040_scaled_baselines_and_ablations"
    assert report["seed"] == 20260917
    protocol = report["protocol"]
    assert protocol["orders"] == [10, 14, 18, 22, 26, 30]
    assert protocol["replicates"] == 6
    assert protocol["graph_families"] == 5
    assert protocol["weight_models"] == ["uniform", "integer", "lognormal", "pareto"]
    assert protocol["baselines"] == list(BASELINES)
    assert len(report["graphs"]) == report["graph_count"] == 180
    records = report["records"]
    assert len(records) == report["weighted_instances"] == 720
    assert len({row["graph_index"] for row in records}) == 180
    assert all(sum(row["weight_model"] == model for row in records) == 180
               for model in protocol["weight_models"])
    for row in records:
        ratios = [row[f"{name}_ratio"] for name in BASELINES]
        assert all(value >= 1 - 2e-8 for value in ratios)
        assert all(ratios[i] + 2e-8 >= ratios[i + 1] for i in range(4))
        assert row["weight_min"] > 0 and row["weight_max"] >= row["weight_min"]
    for baseline in BASELINES:
        check_summary([row[f"{baseline}_ratio"] for row in records],
                      report["baseline_summary"][baseline])

    checks = report["full_blossom_spot_checks"]
    assert len(checks) == 40
    assert {row["root_order"] for row in checks} == {10, 14}
    assert all(math.isclose(row["ratio"], 1.0, abs_tol=2e-8) for row in checks)

    structured = report["structured_ablations"]
    assert len(structured) == 30
    expected = {
        "triangles": (Fraction(3, 2), Fraction(1), Fraction(1), Fraction(1), Fraction(1)),
        "C5": (Fraction(5, 4), Fraction(5, 4), Fraction(1), Fraction(1), Fraction(1)),
        "C7": (Fraction(7, 6), Fraction(7, 6), Fraction(7, 6), Fraction(1), Fraction(1)),
        "C9": (Fraction(9, 8), Fraction(9, 8), Fraction(9, 8), Fraction(9, 8), Fraction(1)),
        "C11": (Fraction(11, 10),) * 5,
        "K5": (Fraction(5, 4),) * 5,
    }
    for row in structured:
        assert row["copies"] in (1, 2, 4, 8, 12)
        actual = tuple(row[f"{name}_ratio"] for name in BASELINES)
        assert all(math.isclose(value, float(target), abs_tol=2e-12)
                   for value, target in zip(actual, expected[row["family"]]))

    scaling = report["non_skew_scaling"]
    assert [row["order"] for row in scaling] == [3, 6, 12, 24, 48, 96]
    for row in scaling:
        blocks = row["triangle_blocks"]
        assert math.isclose(row["max_degree_sum"], 8 / 9, abs_tol=2e-12)
        assert math.isclose(row["odd_set_square_sum"], 4 * blocks / 3, abs_tol=2e-12)
        assert row["matching_bound"] == blocks
        assert math.isclose(row["violation_ratio"], 4 / 3, abs_tol=2e-12)

    tightness = report["theorem_tightness"]
    assert tightness["random"]["count"] == 540
    assert tightness["random"]["max"] < 1
    assert tightness["matching_supported"]["count"] == 180
    assert math.isclose(tightness["matching_supported"]["mean"], 1.0, abs_tol=2e-12)
    for relative, expected_hash in report["artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected_hash
    claims = report["claims"]
    assert claims["experiments_replace_theorem"] is False
    assert claims["full_blossom_spot_checks_all_exact"] is True
    assert claims["bounded_local_constraints_can_leave_persistent_gaps"] is True
    assert claims["non_skew_failure_scales_by_direct_sum"] is True
    return {"status": "C040_scaled_ablations_verified", "graphs": 180,
            "weighted_instances": 720, "full_blossom_spot_checks": 40,
            "structured_rows": 30, "artifact_hashes": len(report["artifacts"])}


def main():
    print(json.dumps(verify(json.loads(REPORT.read_text(encoding="utf-8"))), indent=2))


if __name__ == "__main__":
    main()
