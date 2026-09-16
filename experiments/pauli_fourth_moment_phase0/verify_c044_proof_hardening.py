"""Independent standard-library verifier for the frozen C044 record."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "results" / "pauli_fourth_moment_phase0" / "c044_proof_hardening.json"
SOURCE = ROOT / "experiments" / "pauli_fourth_moment_phase0" / "run_c044_proof_hardening.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recompute_algebra_count(max_order: int) -> int:
    rows = 0
    for order in range(7, max_order + 1):
        for p in range(3, (order - 1) // 2 + 1):
            r = p - 1
            q = order - r
            assert q >= r + 3
            for a in range(1, r + 1):
                for b in range(1, r + 1):
                    if a + b < q:
                        continue
                    h = a + b - q
                    assert 0 <= h <= r - 3
                    assert r < q - 1 < q
                    assert 1 + (r - b) + (r - a) + (h + 2) == 3 * p - order
                    rows += 1
    return rows


def recompute_sumset_subsets(max_h: int) -> int:
    checked = 0
    for h in range(max_h + 1):
        universe = set(range(h + 1))
        for bits in range(1 << (h + 1)):
            x_set = {value for value in universe if bits >> value & 1}
            admissible_y = universe - {h + 1 - value for value in x_set}
            assert all(x + y != h + 1 for x in x_set for y in admissible_y)
            assert len(x_set) + len(admissible_y) <= h + 2
            checked += 1
    return checked


def verify(payload: dict, root: Path = ROOT) -> dict:
    assert payload["experiment"] == "C044_SCF_quasiline_proof_hardening"
    assert payload["status"] == "proof_hardened_and_all_controls_passed"
    assert payload["source_sha256"] == sha256(root / SOURCE.relative_to(ROOT))
    analytic = payload["analytic_result"]
    assert analytic["theorem"] == "Every simplicial claw-free quasi-line graph is rank-perfect."
    assert analytic["external_geometric_lemma_required"] is False
    assert "|K| <= 3p-n" in analytic["new_proof_component"]

    heredity = payload["all_deletions_heredity_audit"]
    assert heredity["graphs"] == 4308
    assert heredity["all_one_vertex_deletions"] == 38772
    assert heredity["failures"] == 0
    census = root / heredity["source"]
    assert heredity["source_sha256"] == sha256(census)

    algebra = payload["algebraic_parameter_audit"]
    assert algebra["max_order"] == 160 and algebra["failures"] == 0
    assert algebra["admissible_maximum_pairs"] == recompute_algebra_count(160)

    sumsets = payload["sumset_disjointness_audit"]
    assert sumsets["max_h"] == 20 and sumsets["failures"] == 0
    assert sumsets["subsets_checked"] == recompute_sumset_subsets(20)

    exact = payload["exact_circulant_clique_audit"]
    assert exact["max_order"] == 30
    assert exact["cliques_enumerated"] > 1_000_000
    assert exact["nonlocal_cliques"] > 0 and exact["tight_nonlocal_cliques"] > 0
    assert exact["simplicial_cliques_p_equals_2"] > 0
    assert exact["simplicial_cliques_p_at_least_3"] == 0
    first = exact["first_nonlocal"]
    assert first["order"] == 9 and first["p"] == 4
    assert first["size"] <= first["bound"]

    dependency = payload["dependency_audit"]
    report = root / dependency["report"]
    assert dependency["report_sha256"] == sha256(report)
    assert all(value is True for key, value in dependency.items() if key.endswith("_checked"))
    report_text = report.read_text(encoding="utf-8")
    for required in ["Definition 8", "Theorem 26", "n>2p>=4", "p-r-1", "unrefereed"]:
        assert required in report_text
    return {
        "status": "C044_verified",
        "all_deletions": heredity["all_one_vertex_deletions"],
        "algebra_rows": algebra["admissible_maximum_pairs"],
        "sumset_subsets": sumsets["subsets_checked"],
        "exact_cliques": exact["cliques_enumerated"],
    }


def main() -> None:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    print(json.dumps(verify(payload), indent=2))


if __name__ == "__main__":
    main()
