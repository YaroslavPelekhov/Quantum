"""Check standalone C038 manuscript claims against the frozen artifact."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TEX = Path(__file__).with_name("main.tex")
DATA = ROOT / "results" / "pauli_fourth_moment_phase0" / "c038_line_graph_hbar.json"


def main():
    text = TEX.read_text(encoding="utf-8")
    report = json.loads(DATA.read_text(encoding="utf-8"))
    required = [
        r"\beta(L(R),w)=\alpha(L(R),w)=\nu(R,w)",
        r"\left(\frac{\norm{A}_*}{2}\right)^2",
        "1245 root graphs",
        "47 direct Jordan--Wigner norm",
        r"L(K_{2k+1})",
        "not an externally reviewed",
        "No quantum advantage",
    ]
    for item in required:
        assert item in text, item
    assert report["atlas_nonempty_roots"] == 1245
    assert report["direct_majorana_norm_cases"] == 47
    assert report["arbitrary_size_theorem"] is True
    assert report["unrestricted_SCF_theorem"] is False
    assert report["A_star_confirmed"] is False
    assert len(report["strict_hperfect_separations"]) == 3
    print(json.dumps({
        "status": "standalone_C038_paper_checked",
        "atlas_roots": report["atlas_nonempty_roots"],
        "direct_majorana_cases": report["direct_majorana_norm_cases"],
        "external_reviewed": False,
        "priority_confirmed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
