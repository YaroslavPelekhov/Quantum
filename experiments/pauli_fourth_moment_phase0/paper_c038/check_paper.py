"""Check standalone manuscript claims against the C038--C043 artifacts."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TEX = Path(__file__).with_name("main.tex")
DATA = ROOT / "results" / "pauli_fourth_moment_phase0" / "c038_line_graph_hbar.json"
ABLATIONS = ROOT / "results" / "pauli_fourth_moment_phase0" / "c039_central_ablations.json"
SCALED = ROOT / "results" / "pauli_fourth_moment_phase0" / "c040_scaled_ablations.json"
DENSITY = ROOT / "results" / "pauli_fourth_moment_phase0" / "c041_density_coupling_stress.json"
BOUNDARY = ROOT / "results" / "pauli_fourth_moment_phase0" / "c042_rank_perfect_boundary.json"
QUASILINE = ROOT / "results" / "pauli_fourth_moment_phase0" / "c043_quasiline_scf_falsification.json"
HARDENING = ROOT / "results" / "pauli_fourth_moment_phase0" / "c044_proof_hardening.json"
PRIORITY = ROOT / "results" / "pauli_fourth_moment_phase0" / "c045_priority_submission_audit.json"


def main():
    text = TEX.read_text(encoding="utf-8")
    report = json.loads(DATA.read_text(encoding="utf-8"))
    ablations = json.loads(ABLATIONS.read_text(encoding="utf-8"))
    scaled = json.loads(SCALED.read_text(encoding="utf-8"))
    density = json.loads(DENSITY.read_text(encoding="utf-8"))
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    quasiline = json.loads(QUASILINE.read_text(encoding="utf-8"))
    hardening = json.loads(HARDENING.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))
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
        "Every rank-perfect simplicial claw-free graph",
        r"H?\textasciigrave{}adQY",
        "4308 SCF graphs",
        "60 connected SCF",
        "c042_rank_perfect_boundary.png",
        "Every simplicial claw-free quasi-line graph is rank-perfect",
        "6162 circulant parameter pairs",
        "18,149 cliques",
        "3,803,174 cliques",
        "4,194,302",
        "oriolostauffer2022",
        "Exact weighted Pauli uncertainty on line graphs",
        "Contribution hierarchy, priority boundary, and conclusion",
        "C045 search",
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
    assert boundary["order9"]["SCF_graphs"] == 4308
    assert boundary["order9"]["quasi_line_non_line_graphs"] == 3048
    assert boundary["strict_witness"]["graph6"] == "H?`adQY"
    assert boundary["strict_witness"]["line_graph"] is False
    assert boundary["strict_witness"]["nonrank_facets"] == 0
    assert boundary["sampled_circular_arc_stress"]["graphs"] == 60
    assert "all SCF quasi-line graphs are rank-perfect" in boundary["scope"]["not_proved"]
    assert quasiline["status"] == "theorem_proved_and_controls_passed"
    assert quasiline["conjecture_proved"] is True
    assert quasiline["circulant_obstruction_audit"]["cases"] == 6162
    assert quasiline["exact_small_circulant_audit"]["cliques_enumerated"] == 18149
    assert quasiline["heredity_audit"]["deterministic_one_vertex_deletions"] == 4308
    assert quasiline["random_proper_circular_arc_attack"]["graphs_tested"] == 250
    assert hardening["status"] == "proof_hardened_and_all_controls_passed"
    assert hardening["all_deletions_heredity_audit"]["all_one_vertex_deletions"] == 38772
    assert hardening["algebraic_parameter_audit"]["admissible_maximum_pairs"] == 1027351
    assert hardening["sumset_disjointness_audit"]["subsets_checked"] == 4194302
    assert hardening["exact_circulant_clique_audit"]["cliques_enumerated"] == 3803174
    assert priority["status"] == "priority_survives_search_not_certified"
    assert priority["sources_checked"] == 9
    assert priority["exact_collision_found"] is False
    assert priority["priority_certified"] is False
    assert priority["manuscript_decisions"]["line_graph_theorem_is_headline"] is True
    print(json.dumps({
        "status": "standalone_C038_C045_paper_checked",
        "atlas_roots": report["atlas_nonempty_roots"],
        "direct_majorana_cases": report["direct_majorana_norm_cases"],
        "weighted_ablation_cases": ablations["weighted_instances"],
        "scaled_weighted_cases": scaled["weighted_instances"],
        "density_weighted_cases": density["density_weighted_instances"],
        "order9_SCF_graphs": boundary["order9"]["SCF_graphs"],
        "C042_sampled_graphs": boundary["sampled_circular_arc_stress"]["graphs"],
        "C043_circulant_cases": quasiline["circulant_obstruction_audit"]["cases"],
        "C043_exact_small_cliques": quasiline["exact_small_circulant_audit"]["cliques_enumerated"],
        "C043_random_CFI_controls": quasiline["random_proper_circular_arc_attack"]["graphs_tested"],
        "C044_all_deletions": hardening["all_deletions_heredity_audit"]["all_one_vertex_deletions"],
        "C044_exact_cliques": hardening["exact_circulant_clique_audit"]["cliques_enumerated"],
        "C045_sources_checked": priority["sources_checked"],
        "full_polytope_exact_fraction": ablations["baseline_summary"]["full_matching"]["exact_fraction"],
        "external_reviewed": False,
        "priority_confirmed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
