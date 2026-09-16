"""Independent standard-library verifier for the frozen C041 stress report."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "results" / "pauli_fourth_moment_phase0" / "c041_density_coupling_stress.json"


def verify(report):
    assert report["experiment"] == "C041_density_and_weak_coupling_stress"
    assert report["seed"] == 20260918
    assert report["protocol"] == {
        "orders": [20, 30, 40], "expected_degrees": [2, 3, 4, 5, 6],
        "replicates": 3, "weight_models": ["uniform", "integer"],
    }
    assert len(report["graphs"]) == report["density_graphs"] == 45
    records = report["density_records"]
    assert len(records) == report["density_weighted_instances"] == 90
    assert len({row["graph_index"] for row in records}) == 45
    assert all(row["degree_ratio"] + 2e-8 >= row["clique_ratio"] >= 1 - 2e-8
               for row in records)
    assert all(row["clique_ratio"] + 2e-8 >= row["odd9_ratio"] >= 1 - 2e-8
               for row in records)
    strict_odd9 = [row for row in records if row["odd9_ratio"] > 1 + 1e-8]
    assert len(strict_odd9) == 5
    assert math.isclose(max(row["odd9_ratio"] for row in records), 29 / 28,
                        abs_tol=2e-12)
    assert max(row["cycles5"] + row["cycles7"] + row["cycles9"] for row in records) == 384484

    coupling = report["coupling_ablations"]
    assert len(coupling) == report["coupling_instances"] == 28
    for row in coupling:
        blocks = row["blocks"]
        epsilon = row["bridge_weight"]
        expected_matching = 2 * blocks + epsilon * blocks / 2
        expected_ratio = (2.5 * blocks) / expected_matching
        assert blocks in (2, 4, 8, 16)
        assert row["root_order"] == 5 * blocks
        assert math.isclose(row["matching"], expected_matching, abs_tol=2e-10)
        for baseline in ("degree", "clique", "odd9"):
            assert math.isclose(row[f"{baseline}_ratio"], expected_ratio, abs_tol=2e-10)
    for blocks in (2, 4, 8, 16):
        selected = [row for row in coupling if row["blocks"] == blocks]
        ratios = [row["odd9_ratio"] for row in selected]
        assert all(ratios[i] > ratios[i + 1] - 2e-12 for i in range(len(ratios) - 1))
        assert math.isclose(ratios[0], 1.25, abs_tol=2e-12)
        assert math.isclose(ratios[-1], 1.0, abs_tol=2e-12)

    assert len(report["density_summary"]) == 30
    for relative, expected_hash in report["artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected_hash
    assert report["claims"]["local_gap_depends_on_density"] is True
    assert report["claims"]["planted_blossom_gap_survives_weak_coupling"] is True
    assert report["claims"]["experiments_replace_theorem"] is False
    return {"status": "C041_density_coupling_stress_verified", "density_graphs": 45,
            "density_weighted_instances": 90, "strict_odd9_instances": 5,
            "coupling_instances": 28, "artifact_hashes": len(report["artifacts"])}


def main():
    print(json.dumps(verify(json.loads(REPORT.read_text(encoding="utf-8"))), indent=2))


if __name__ == "__main__":
    main()
