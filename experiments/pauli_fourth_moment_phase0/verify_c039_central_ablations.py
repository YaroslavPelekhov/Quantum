"""Standard-library verifier for the frozen C039 baseline/ablation report."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "results" / "pauli_fourth_moment_phase0" / "c039_central_ablations.json"


def quantile(values, q):
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
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
    assert report["experiment"] == "C039_central_mechanism_baselines_and_ablations"
    assert report["seed"] == 20260916
    assert report["atlas_root_graphs"] == 1245
    assert report["weight_vectors_per_graph"] == 5
    records = report["records"]
    assert len(records) == report["weighted_instances"] == 6225
    assert len({row["graph6"] for row in records}) == 1245
    for row in records:
        assert len(row["weights"]) == row["root_edges"]
        assert all(isinstance(value, int) and 1 <= value <= 9 for value in row["weights"])
        assert row["degree_ratio"] >= 1 - 2e-8
        assert row["h_ratio"] >= 1 - 2e-8
        assert math.isclose(row["full_ratio"], 1.0, abs_tol=2e-8)
        assert row["degree_ratio"] + 2e-8 >= row["h_ratio"]
        assert row["h_ratio"] + 2e-8 >= row["full_ratio"]

    fields = {
        "degree_only": "degree_ratio",
        "h_relaxation": "h_ratio",
        "full_matching": "full_ratio",
    }
    for baseline, field in fields.items():
        check_summary([row[field] for row in records], report["baseline_summary"][baseline])

    bipartite = [row for row in records if row["bipartite_root"]]
    nonbipartite = [row for row in records if not row["bipartite_root"]]
    assert len(bipartite) == 710 and len(nonbipartite) == 5515
    for name, selected in (("bipartite_roots", bipartite), ("nonbipartite_roots", nonbipartite)):
        frozen = report["baseline_summary_by_graph_class"][name]
        assert frozen["instances"] == len(selected)
        for baseline, field in fields.items():
            check_summary([row[field] for row in selected], frozen[baseline])
    assert all(math.isclose(row["degree_ratio"], 1.0, abs_tol=2e-8) for row in bipartite)

    for baseline, field in (("degree_only", "degree_ratio"), ("h_relaxation", "h_ratio")):
        strict = [row for row in records if row[field] > 1 + 1e-8]
        frozen = report["strictness_counts"][baseline]
        assert frozen["strict_instances"] == len(strict)
        assert frozen["strict_root_graphs"] == len({row["graph6"] for row in strict})
        assert math.isclose(frozen["fraction_of_weighted_instances"], len(strict) / len(records), abs_tol=2e-12)

    householder = report["skewness_ablation"]
    matrix = [[Fraction(item) for item in row] for row in householder["matrix"]]
    product = [[sum(matrix[k][i] * matrix[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    assert product == [[Fraction(int(i == j)) for j in range(3)] for i in range(3)]
    squares = [matrix[0][1] ** 2, matrix[0][2] ** 2, matrix[1][2] ** 2]
    assert squares == [Fraction(4, 9)] * 3
    assert max(squares[0] + squares[1], squares[0] + squares[2], squares[1] + squares[2]) == Fraction(8, 9)
    assert sum(squares) == Fraction(4, 3) > 1
    assert householder["K3_odd_set_sum"] == "4/3"
    control = report["skew_control"]
    assert sum(Fraction(value) for value in control["edge_squares"]) == 1

    family_rows = report["family_ablations"]
    assert len(family_rows) == 10
    for row in family_rows:
        order = row["root_order"]
        assert order in (5, 7, 9, 11, 13) and order % 2 == 1
        matching = Fraction(order - 1, 2)
        degree = Fraction(order, 2)
        expected_h = degree if row["family"] == "odd_complete" else matching
        assert Fraction(str(row["matching"])) == matching
        assert Fraction(str(row["degree_lp"])) == degree
        assert Fraction(str(row["h_relaxation"])) == expected_h
        assert Fraction(str(row["full_matching"])) == matching

    assert report["theorem_tightness"]["matching_supported"]["count"] == 1245
    assert math.isclose(report["theorem_tightness"]["matching_supported"]["mean"], 1.0, abs_tol=2e-12)
    assert report["theorem_tightness"]["nontrivial_random_directions"]["median"] < 0.5
    for relative, expected in report["artifacts"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative

    claims = report["claims"]
    assert claims["full_matching_matches_exact_every_instance"] is True
    assert claims["skewness_is_necessary_for_the_contraction_lemma"] is True
    assert claims["matching_supported_directions_attain_the_bound"] is True
    assert claims["experiments_replace_analytic_proof"] is False
    return {
        "status": "C039_baselines_ablations_and_artifacts_verified",
        "weighted_instances": len(records),
        "degree_strict_instances": report["strictness_counts"]["degree_only"]["strict_instances"],
        "h_strict_instances": report["strictness_counts"]["h_relaxation"]["strict_instances"],
        "artifact_hashes": len(report["artifacts"]),
    }


def main():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    print(json.dumps(verify(report), indent=2))


if __name__ == "__main__":
    main()
