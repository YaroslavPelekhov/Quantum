"""Independent standard-library audit of the exact C038 separation records."""
from __future__ import annotations

import hashlib
import itertools as it
import json
from fractions import Fraction as F
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "results" / "pauli_fourth_moment_phase0"
NOTE = Path(__file__).with_name("LINE_GRAPH_HBAR_THEOREM_C038.md")


def verify(report: dict) -> dict:
    assert report["experiment"] == "C038_line_graph_hbar_matrix_audit"
    assert report["theorem_note_sha256"] == hashlib.sha256(NOTE.read_bytes()).hexdigest()
    assert report["arbitrary_size_theorem"] is True
    assert report["unrestricted_SCF_theorem"] is False
    assert report["A_star_confirmed"] is False
    witnesses = report["strict_hperfect_separations"]
    assert [row["root_order"] for row in witnesses] == [5, 7, 9]
    for row in witnesses:
        n = row["root_order"]
        assert n >= 5 and n % 2 == 1
        k = (n - 1) // 2
        x = F(1, n - 1)
        edges = list(it.combinations(range(n), 2))
        assert row["root"] == f"K{n}"
        assert row["line_graph_order"] == len(edges) == n * (n - 1) // 2
        assert F(row["coordinate"]) == x
        assert F(row["star_value"]) == (n - 1) * x == 1
        assert F(row["triangle_value"]) == 3 * x <= 1
        for length in range(5, n + 1, 2):
            assert length * x <= F(length - 1, 2)
        assert row["matching_bound"] == k
        assert F(row["total_value"]) == len(edges) * x == F(n, 2)
        assert F(row["total_value"]) - k == F(row["h_relaxation_gap"]) == F(1, 2)
        assert row["hbar_perfect_by_C038"] is True
    assert report["atlas_nonempty_roots"] == len(report["records"])
    assert report["max_root_order"] == 7
    assert 0 <= report["max_ratio_to_proved_bound"] <= 1 + 1e-8
    assert report["direct_majorana_norm_cases"] > 0
    assert report["max_direct_majorana_norm_error"] <= 1e-9
    assert report["max_degree_excess"] <= 1e-8
    assert report["max_odd_set_excess"] <= 1e-8
    return {
        "status": "C038_exact_separation_and_frozen_stress_summary_verified",
        "atlas_nonempty_roots": report["atlas_nonempty_roots"],
        "direct_majorana_norm_cases": report["direct_majorana_norm_cases"],
        "strict_infinite_family_templates": len(witnesses),
        "arbitrary_size_theorem": True,
        "unrestricted_SCF_theorem": False,
        "A_star_confirmed": False,
    }


if __name__ == "__main__":
    result = verify(json.loads((DATA / "c038_line_graph_hbar.json").read_text()))
    print(json.dumps(result, indent=2))
