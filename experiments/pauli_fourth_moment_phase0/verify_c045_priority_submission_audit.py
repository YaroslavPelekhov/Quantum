"""Verify the frozen C045 priority and submission-focus audit."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPORT = HERE / "C045_PRIORITY_AND_SUBMISSION_AUDIT.md"
RECORD = ROOT / "results" / "pauli_fourth_moment_phase0" / "c045_priority_submission_audit.json"
TEX = HERE / "paper_c038" / "main.tex"


def verify(record_path=RECORD, report_path=REPORT, tex_path=TEX):
    data = json.loads(Path(record_path).read_text(encoding="utf-8"))
    report = Path(report_path).read_text(encoding="utf-8")
    tex = Path(tex_path).read_text(encoding="utf-8")
    assert data["cycle"] == "C045"
    assert data["status"] == "priority_survives_search_not_certified"
    assert data["sources_checked"] == 9
    assert data["exact_collision_found"] is False
    assert data["priority_certified"] is False
    assert data["external_reviewed"] is False
    assert data["section7_proof_hardened_by_c044"] is True
    assert all(data["manuscript_decisions"].values())
    digest = hashlib.sha256(report.encode("utf-8")).hexdigest()
    assert data["report_sha256"] == digest
    for needle in (
        "BETA(L(R))=MATCH(R)",
        "Surviving priority-sensitive package",
        "Claims explicitly removed from the novelty surface",
        "Priority is supported, not certified",
        "3,803,174 exact circulant cliques",
    ):
        assert needle in report, needle
    assert "Exact weighted Pauli uncertainty on line graphs" in tex
    assert "Secondary extension beyond line graphs" in tex
    assert "Contribution hierarchy, priority boundary, and conclusion" in tex
    assert tex.index("Contribution hierarchy, priority boundary, and conclusion") < tex.index(r"\appendix")
    assert tex.index(r"\appendix") < tex.index("Scaling, density, and weak coupling")
    assert "No quantum advantage or new matching algorithm is claimed." in tex
    for overclaim in ("we are the first", "this is definitively novel", "priority is certified"):
        assert overclaim not in tex.lower()
    return {
        "status": "c045_priority_submission_audit_verified",
        "sources_checked": data["sources_checked"],
        "exact_collision_found": False,
        "priority_certified": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
