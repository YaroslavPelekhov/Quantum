"""Verify the frozen C046 mock-referee and beta-body audit."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPORT = HERE / "C046_MOCK_REFEREE_BODY_AUDIT.md"
RECORD = ROOT / "results" / "pauli_fourth_moment_phase0" / "c046_mock_referee_body_audit.json"
TEX = HERE / "paper_c038" / "main.tex"


def verify(record_path=RECORD, report_path=REPORT, tex_path=TEX):
    data = json.loads(Path(record_path).read_text(encoding="utf-8"))
    report = Path(report_path).read_text(encoding="utf-8")
    tex = Path(tex_path).read_text(encoding="utf-8")
    assert data["cycle"] == "C046"
    assert data["status"] == "central_proof_survives_mock_referee"
    assert data["critical_findings"] == 0
    assert data["resolved_findings"] == 6
    assert data["headline_internal_gaps_remaining"] == 0
    assert data["external_reviewed"] is False
    assert data["priority_certified"] is False
    assert all(
        data[key] is True
        for key in (
            "body_definition_added",
            "raw_range_distinguished_from_beta_body",
            "body_equality_proved_by_support_functions",
            "odd_clifford_case_explicit",
            "representation_quantifier_repaired",
            "secondary_extension_independent",
        )
    )
    digest = hashlib.sha256(report.encode("utf-8")).hexdigest()
    assert data["report_sha256"] == digest
    for needle in (
        "The skew-contraction lemma",
        "Central proof dependency audit",
        "No step uses the finite atlas",
        "mock review is not a substitute for an independent referee",
    ):
        assert needle in report, needle
    for needle in (
        r"\newcommand{\BETA}{\operatorname{BETA}}",
        r"\BETA(G)=\operatorname{conv}(\mathord\downarrow\mathcal Q(\mathcal S))",
        r"\boxed{\BETA(L(R))=\MATCH(R).}",
        "Compact convex corners are determined by their nonnegative",
        "also for odd-order roots",
        "raw joint range",
    ):
        assert needle in tex, needle
    assert r"\sup_{\{P_i\},\rho}" not in tex
    return {
        "status": "c046_mock_referee_body_audit_verified",
        "resolved_findings": data["resolved_findings"],
        "headline_internal_gaps_remaining": 0,
        "external_reviewed": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
