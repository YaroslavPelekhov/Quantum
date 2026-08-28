"""Audit and summarize the frozen causal shadow-price controller runs."""
from __future__ import annotations
import hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "causal_certification_debt"
COT = REPO / "results" / "compressed_observable_telescope"
OBS = REPO / "results" / "observable_telescope"
MANUAL = REPO / "results" / "decision_certified_bond_allocation" / "summary.json"
RUNS = {
    "ibm32_sorted": RESULTS / "controller_ibm32_confirm_sorted.json",
    "ibm32_spectral": RESULTS / "controller_ibm32_confirm_spectral.json",
    "chesapeake_sorted": RESULTS / "controller_chesapeake_confirm_sorted.json",
}
FIRST = {
    "ibm32_sorted": COT / "compressed_first_term_ibm32_confirm_sorted_adaptive.json",
    "ibm32_spectral": COT / "compressed_first_term_ibm32_confirm_spectral_adaptive.json",
}

def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))

def atomic_json(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)

def reference(label):
    if label in FIRST:
        x = read(FIRST[label])["pair_rows"][0]
        return x["compressed_first_term_pair_sum"], x["mps_gap_absolute"], "compressed COT"
    rows = read(OBS / "pair_rows.json")["rows"]
    x = next(x for x in rows if (x["case"], x["setting"], x["ordering"]) == ("chesapeake", "confirm", "sorted"))
    return x["telescope_pair_width"], abs(x["mps_delta"]), "exact telescope"

def audit_method(row):
    score_bad = op_bad = residual_bad = dense = 0
    bonds, debts = [], []
    for cp in row["checkpoints"]:
        candidates = cp["candidate_diagnostics"]
        expected = min(candidates, key=lambda x: (x["score"], x["bond"]))["bond"]
        chosen = cp["chosen_residual_bond"]
        bonds.append(chosen); score_bad += chosen != expected
        debts.append(next(x for x in candidates if x["bond"] == chosen)["causal_debt_increment"])
        if "oracle_actual_operator_error" in cp:
            dense += 1
            op_bad += cp["oracle_actual_operator_error"] > cp["eta_operator_norm_upper_bound"] + 1e-9
            residual_bad += sum(a > b + 1e-9 for a, b in zip(cp["oracle_residual_representation_errors"], cp["discarded_residual_tail_bounds"]))
    return {
        "method": row["method"], "bond_counts": row["bond_counts"],
        "bond_transitions": sum(a != b for a, b in zip(bonds, bonds[1:])),
        "work_ratio_vs_fixed_R256": row["cubic_work_ratio_vs_fixed_R256"],
        "causal_debt": row["causal_debt"], "operator_correction": row["operator_correction_sum"],
        "debt_reconstruction_error": abs(math.fsum(debts) - row["causal_debt"]),
        "score_argmin_violations": score_bad, "dense_checkpoints_audited": dense,
        "dense_operator_violations": op_bad, "dense_residual_violations": residual_bad,
    }

def audit_run(label, payload):
    methods = [audit_method(x) for x in payload["rows"]]
    first, gap, source = reference(label)
    correction = math.fsum(x["operator_correction"] for x in methods)
    work = math.fsum(x["work_ratio_vs_fixed_R256"] for x in methods) / 2
    width = first + correction
    return {
        "label": label, "case": payload["case"], "ordering": payload["ordering"],
        "setting": payload["setting"], "complete": payload["complete"],
        "shadow_price": payload["controller"]["shadow_price"],
        "candidate_bonds": payload["controller"]["candidate_bonds"],
        "uses_dense_exact_errors_for_selection": payload["controller"]["uses_dense_exact_errors_for_selection"],
        "first_term_source": source, "first_term_pair": first,
        "operator_correction_pair": correction, "certified_pair_width": width,
        "mps_gap": gap, "certificate_margin": gap-width, "certified": width < gap,
        "paired_work_ratio_vs_fixed_R256_R256": work,
        "paired_work_saving_fraction": 1-work, "methods": methods,
    }

def build_summary():
    runs = [audit_run(k, read(v)) for k, v in RUNS.items()]
    by = {x["label"]: x for x in runs}; manual = read(MANUAL)
    methods = [m for r in runs for m in r["methods"]]
    s, p = by["ibm32_sorted"], by["ibm32_spectral"]
    return {
        "stage": "frozen_causal_shadow_price_controller_audit", "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy_class": "fixed primary schedule; residual bonds {128,256,512}; greedy cost-plus-causal-debt score; lambda=500",
        "dcc_interpretation": "Certified work is a feasible upper bound on decision-certification cost in this policy class, not a global minimum.",
        "runs": runs, "comparisons": {
            "sorted_controller_work_vs_manual": s["paired_work_ratio_vs_fixed_R256_R256"] / manual["sorted_causal_asymmetric"]["paired_cubic_work_ratio_vs_R256_R256"],
            "spectral_controller_work_vs_manual": p["paired_work_ratio_vs_fixed_R256_R256"] / manual["spectral_frozen_transfer"]["paired_cubic_work_ratio_vs_R256_R256"],
            "spectral_controller_work_multiple_vs_all_R128": p["paired_work_ratio_vs_fixed_R256_R256"] / .125,
        }, "audit_totals": {
            "score_argmin_violations": sum(x["score_argmin_violations"] for x in methods),
            "dense_checkpoints_audited": sum(x["dense_checkpoints_audited"] for x in methods),
            "dense_operator_violations": sum(x["dense_operator_violations"] for x in methods),
            "dense_residual_violations": sum(x["dense_residual_violations"] for x in methods),
            "maximum_debt_reconstruction_error": max(x["debt_reconstruction_error"] for x in methods),
        }}

def report(summary):
    lines = [
        "# Frozen causal shadow-price controller", "",
        "The controller was calibrated once on `ibm32/confirm/sorted` with `lambda=500`, then frozen for spectral ordering and a separate QOBLIB graph. Dense exact errors are audit-only.", "",
        "| run | LR 128/256/512 | MR 128/256/512 | width | gap | margin | work | saving |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in summary["runs"]:
        lr, mr = r["methods"]
        fmt = lambda x: "/".join(str(x["bond_counts"][str(b)]) for b in (128,256,512))
        lines.append(f"| {r['label']} | {fmt(lr)} | {fmt(mr)} | {r['certified_pair_width']:.6f} | {r['mps_gap']:.6f} | {r['certificate_margin']:.6f} | {r['paired_work_ratio_vs_fixed_R256_R256']:.4f} | {100*r['paired_work_saving_fraction']:.2f}% |")
    a, c = summary["audit_totals"], summary["comparisons"]
    lines += ["", "## Audit", "",
        f"Score-argmin violations: `{a['score_argmin_violations']}`; operator violations: `{a['dense_operator_violations']}`; residual violations: `{a['dense_residual_violations']}` across `{a['dense_checkpoints_audited']}` dense checkpoints. Maximum debt reconstruction error: `{a['maximum_debt_reconstruction_error']:.3e}`.",
        "", "## Claim boundary", "", summary["dcc_interpretation"],
        f"The frozen spectral policy is `{c['spectral_controller_work_vs_manual']:.3f}x` the manual transfer, but still `{c['spectral_controller_work_multiple_vs_all_R128']:.3f}x` an all-R128 pair that already certifies spectral. Transfer soundness is shown; global resource optimality is not."]
    return "\n".join(lines) + "\n"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def write_manifest():
    sources = [HERE/x for x in ("THEOREMS.md", "NOVELTY_POSITIONING.md", "CONTROLLER_PROTOCOL.md", "run_shadow_price_controller.py", "analyze_controller.py", "test_controller.py", "README.md")]
    inputs = list(RUNS.values()) + list(FIRST.values()) + [OBS/"pair_rows.json", MANUAL]
    artifacts = [RESULTS/"controller_summary.json", RESULTS/"CONTROLLER_REPORT.md"]
    item = lambda p: {"bytes": p.stat().st_size, "sha256": sha(p)}
    atomic_json(RESULTS/"CONTROLLER_MANIFEST.json", {"complete": True, "created_at": datetime.now(timezone.utc).isoformat(), "sources": {p.relative_to(REPO).as_posix(): item(p) for p in sources}, "inputs": {p.relative_to(REPO).as_posix(): item(p) for p in inputs}, "artifacts": {p.relative_to(REPO).as_posix(): item(p) for p in artifacts}})

def main():
    summary = build_summary()
    atomic_json(RESULTS/"controller_summary.json", summary)
    (RESULTS/"CONTROLLER_REPORT.md").write_text(report(summary), encoding="utf-8")
    write_manifest()
    print(json.dumps(summary, indent=2))

if __name__ == "__main__": main()
