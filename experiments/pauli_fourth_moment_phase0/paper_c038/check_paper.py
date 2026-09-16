"""Check standalone manuscript claims against the C038--C041 artifacts."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TEX = Path(__file__).with_name("main.tex")
DATA = ROOT / "results" / "pauli_fourth_moment_phase0" / "c038_line_graph_hbar.json"
ABLATIONS = ROOT / "results" / "pauli_fourth_moment_phase0" / "c039_central_ablations.json"
SCALED = ROOT / "results" / "pauli_fourth_moment_phase0" / "c040_scaled_ablations.json"
DENSITY = ROOT / "results" / "pauli_fourth_moment_phase0" / "c041_density_coupling_stress.json"


def main():
    text = TEX.read_text(encoding="utf-8")
    report = json.loads(DATA.read_text(encoding="utf-8"))
    ablations = json.loads(ABLATIONS.read_text(encoding="utf-8"))
    scaled = json.loads(SCALED.read_text(encoding="utf-8"))
    density = json.loads(DENSITY.read_text(encoding="utf-8"))
    required = [
        r"\beta(L(R),w)=\alpha(L(R),w)=\nu(R,w)",
        r"\left(\frac{\norm{A}_*}{2}\right)^2",
        "1245 root graphs",
        "47 small-root cases",
        r"L(K_{2k+1})",
        "not an externally reviewed",
        "No quantum advantage",
        "6225 weighted",
        "66.89\\%",
        "84.69\\%",
        "Householder",
        "953 strict cases",
        "4980 seeded Gaussian",
        "c039_baseline_gaps.png",
        "c039_mechanism_ablations.png",
        "720 weighted instances",
        "384,484 enumerated odd cycles",
        "c040_scaled_random_ablations.png",
        "c040_structured_and_tightness.png",
        "c041_density_coupling_stress.png",
    ]
    for item in required:
        assert item in text, item
    assert report["atlas_nonempty_roots"] == 1245
    assert report["direct_majorana_norm_cases"] == 47
    assert report["arbitrary_size_theorem"] is True
    assert report["unrestricted_SCF_theorem"] is False
    assert report["A_star_confirmed"] is False
    assert len(report["strict_hperfect_separations"]) == 3
    assert ablations["atlas_root_graphs"] == 1245
    assert ablations["weighted_instances"] == 6225
    assert ablations["strictness_counts"]["degree_only"]["strict_instances"] == 2061
    assert ablations["strictness_counts"]["h_relaxation"]["strict_instances"] == 953
    assert ablations["baseline_summary"]["full_matching"]["exact_fraction"] == 1.0
    assert ablations["baseline_summary_by_graph_class"]["bipartite_roots"]["instances"] == 710
    assert ablations["skewness_ablation"]["K3_odd_set_sum"] == "4/3"
    assert ablations["skew_control"]["K3_odd_set_sum"] == "1"
    assert ablations["claims"]["experiments_replace_analytic_proof"] is False
    assert scaled["graph_count"] == 180
    assert scaled["weighted_instances"] == 720
    assert len(scaled["full_blossom_spot_checks"]) == 40
    assert scaled["baseline_summary"]["odd9"]["exact_fraction"] > 0.93
    assert scaled["theorem_tightness"]["matching_supported"]["count"] == 180
    assert density["density_graphs"] == 45
    assert density["density_weighted_instances"] == 90
    assert len(density["coupling_ablations"]) == 28
    print(json.dumps({
        "status": "standalone_C038_paper_checked",
        "atlas_roots": report["atlas_nonempty_roots"],
        "direct_majorana_cases": report["direct_majorana_norm_cases"],
        "weighted_ablation_cases": ablations["weighted_instances"],
        "scaled_weighted_cases": scaled["weighted_instances"],
        "density_weighted_cases": density["density_weighted_instances"],
        "full_polytope_exact_fraction": ablations["baseline_summary"]["full_matching"]["exact_fraction"],
        "external_reviewed": False,
        "priority_confirmed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
