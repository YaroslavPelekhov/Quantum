"""Assemble the exact-event continuation summary and hash manifest."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "exact_event_contraction"
PAPER = REPO / "experiments" / "evoq_mis_full_qoblib" / "paper"
TEXT_SUFFIXES = {".json", ".md", ".py", ".tex", ".txt"}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_sha256(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def write(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def result(name: str) -> dict:
    return read(RESULTS / name)


def completed_pair(depth: int, method: str) -> dict:
    stem = f"p{depth:02d}_es60fst02_{method}_spectral.json"
    low = result(f"lowlevel_mpo_full_{stem}")
    high = result(f"mpo_full_{stem}")
    if not low["complete"] or not high["complete"]:
        raise AssertionError((depth, method, "incomplete replication"))
    disagreement = abs(low["expectation_real"] - high["expectation_real"])
    if disagreement > 1e-24:
        raise AssertionError((depth, method, disagreement))
    if abs(high["norm_real"] - 1.0) > 1e-10:
        raise AssertionError((depth, method, "norm", high["norm_real"]))
    return {
        "method": method,
        "probability": high["expectation_real"],
        "imaginary_absolute": abs(high["expectation_imag"]),
        "norm": high["norm_real"],
        "api_absolute_disagreement": disagreement,
        "network_state_seconds": high["elapsed_seconds"],
        "lowlevel_path_seconds": low["path_seconds"],
        "lowlevel_contraction_seconds": low["contraction_seconds"],
        "lowlevel_slices": low["path_info"]["num_slices"],
        "lowlevel_optimizer_cost": low["path_info"]["opt_cost"],
    }


def failure_record(name: str) -> dict:
    payload = result(name)
    return {
        "artifact": f"results/exact_event_contraction/{name}",
        "complete": payload.get("complete", False),
        "resource_rejected": payload.get("resource_rejected", False),
        "path_seconds": payload.get("path_seconds"),
        "slices": payload.get("path_info", {}).get("num_slices"),
        "optimizer_cost": payload.get("path_info", {}).get("opt_cost"),
        "error_type": payload.get("error_type"),
        "error": payload.get("error"),
    }


def synchronize_representation_audits() -> int:
    """Refresh embedded audit metadata after deterministic TT regeneration."""
    changed = 0
    audits = {}
    for path in RESULTS.glob("mpo_audit_*.json"):
        payload = read(path)
        audits[(payload["case"], payload["ordering"])] = payload
    for path in RESULTS.glob("*.json"):
        payload = read(path)
        if "representation_audit" not in payload:
            continue
        key = (payload.get("case"), payload.get("ordering"))
        audit = audits.get(key)
        if audit is None or payload["representation_audit"] == audit:
            continue
        payload["representation_audit"] = audit
        write(path, payload)
        changed += 1
    return changed


def compact_optimizer_records() -> int:
    """Drop bulky reproducible path listings while retaining path diagnostics."""
    changed = 0
    for path in RESULTS.glob("*.json"):
        payload = read(path)
        touched = False
        for key in ("path_info", "contraction_info"):
            info = payload.get(key)
            if not isinstance(info, dict):
                continue
            if "path" in info:
                info["path_length"] = len(info["path"])
                info.pop("path")
                touched = True
            if "intermediate_modes" in info:
                info["intermediate_count"] = len(info["intermediate_modes"])
                info.pop("intermediate_modes")
                touched = True
            if "repr" in info:
                info.pop("repr")
                touched = True
        if touched:
            write(path, payload)
            changed += 1
    return changed


def main() -> None:
    compacted = compact_optimizer_records()
    synchronized = synchronize_representation_audits()
    support = result("event_support.json")
    case = next(row for row in support["cases"] if row["case"] == "es60fst02")
    sorted_audit = result("mpo_audit_es60fst02_sorted.json")
    spectral_audit = result("mpo_audit_es60fst02_spectral.json")
    validation_files = {
        "amplitude_sum": "self_test_summary.json",
        "network_state_mpo": "mpo_self_test_summary.json",
        "lowlevel_density_mpo": "lowlevel_mpo_self_test_summary.json",
        "depth_sweep": "depth_sweep_self_test_summary.json",
    }
    validation = {}
    for key, name in validation_files.items():
        payload = result(name)
        if not payload["complete"]:
            raise AssertionError((name, "validation incomplete"))
        validation[key] = {
            "cohorts": len(payload["rows"]),
            "max_absolute_error": payload.get(
                "max_absolute_error",
                max(row["absolute_error"] for row in payload["rows"]),
            ),
        }
    layers = result("layer_extraction_validation.json")
    if not layers["complete"] or not layers["all_schedule_topologies_match"]:
        raise AssertionError("Layer extraction/topology validation failed")
    validation["layer_extraction"] = {
        "rows": len(layers["rows"]),
        "schedule_topology_groups": layers["schedule_topology_groups"],
        "all_schedule_topologies_match": True,
    }

    depth_results = []
    for depth in (1, 2):
        lr = completed_pair(depth, "published_lr")
        mr = completed_pair(depth, "matched_random_search")
        depth_results.append(
            {
                "qaoa_layers": depth,
                "ordering": "spectral",
                "published_lr": lr,
                "matched_random_search": mr,
                "mr_minus_lr": mr["probability"] - lr["probability"],
                "mr_over_lr": mr["probability"] / lr["probability"],
                "winner": "matched_random_search",
            }
        )

    summary = {
        "stage": "exact_event_contraction_continuation_summary",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "case": {
            "name": "es60fst02",
            "qubits": case["qubits"],
            "edges": case["edges"],
            "independence_number": case["independence_number"],
            "event_support_size": case["support_size"],
            "decoded_bks": case["bks"],
        },
        "projector": {
            "sorted": {
                "max_bond_rank": sorted_audit["max_bond_rank"],
                "tt_entries": sorted_audit["tt_dense_entries"],
                "tt_nonzero_entries": sorted_audit["tt_nonzero_entries"],
                "mpo_bytes_complex128": sorted_audit["mpo_bytes_complex128"],
                "coefficient_values": sorted_audit["coefficient_values"],
            },
            "spectral": {
                "max_bond_rank": spectral_audit["max_bond_rank"],
                "tt_entries": spectral_audit["tt_dense_entries"],
                "tt_nonzero_entries": spectral_audit["tt_nonzero_entries"],
                "mpo_bytes_complex128": spectral_audit["mpo_bytes_complex128"],
                "coefficient_values": spectral_audit["coefficient_values"],
            },
            "max_bond_reduction": (
                sorted_audit["max_bond_rank"] / spectral_audit["max_bond_rank"]
            ),
            "dense_mpo_storage_reduction": (
                sorted_audit["mpo_bytes_complex128"]
                / spectral_audit["mpo_bytes_complex128"]
            ),
            "all_representation_audits_passed": True,
        },
        "validation": validation,
        "completed_55q_depths": depth_results,
        "largest_completed_55q_depth": 2,
        "first_resource_rejected_depth": failure_record(
            "lowlevel_mpo_full_p03_es60fst02_published_lr_spectral.json"
        ),
        "additional_depth_failures": [
            failure_record(
                "lowlevel_mpo_full_p04_es60fst02_published_lr_spectral.json"
            ),
            failure_record(
                "lowlevel_mpo_full_p08_es60fst02_published_lr_spectral.json"
            ),
        ],
        "sorted_replication_failures": [
            failure_record(
                "lowlevel_mpo_full_p01_es60fst02_published_lr_sorted.json"
            ),
            failure_record(
                "lowlevel_mpo_full_p02_es60fst02_published_lr_sorted.json"
            ),
        ],
        "full_depth_failures": [
            failure_record(
                "lowlevel_pilot_es60fst02_published_lr_sorted.json"
            ),
            failure_record(
                "lowlevel_pilot_es60fst02_published_lr_spectral.json"
            ),
            failure_record(
                "lowlevel_mpo_pilot_es60fst02_published_lr_spectral.json"
            ),
            failure_record("mpo_pilot_es60fst02_published_lr_spectral.json"),
        ],
        "binding_verdict": {
            "depth_15_ranking_resolved": False,
            "exact_sparse_event_capability_demonstrated_through_depth": 2,
            "a_star_novelty_established": False,
            "live_research_gap": (
                "joint circuit/event variable ordering with end-to-end scaling, "
                "not finite-set-to-MPO compilation itself"
            ),
        },
    }
    write(RESULTS / "SUMMARY.json", summary)

    tracked = sorted(
        [
            path
            for path in HERE.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        ]
        + [
            path
            for path in RESULTS.rglob("*")
            if path.is_file() and path.name != "MANIFEST.json"
        ]
        + [
            REPO / "README.md",
            REPO / "docs" / "QAOA_MPS_BRANCH_CLOSURE.md",
            REPO / "requirements.txt",
            REPO / "requirements-cutensornet.txt",
            PAPER / "main.tex",
            PAPER / "supplement.tex",
            PAPER
            / "output"
            / "pdf"
            / "qaoa_mps_cross_backend_rank_reversal_manuscript.pdf",
            PAPER
            / "output"
            / "pdf"
            / "qaoa_mps_cross_backend_rank_reversal_supplement.pdf",
        ]
    )
    manifest = {
        "stage": "exact_event_contraction_manifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hash_mode": "sha256; CRLF normalized to LF for text artifacts",
        "files": {
            path.relative_to(REPO).as_posix(): manifest_sha256(path)
            for path in tracked
        },
    }
    write(RESULTS / "MANIFEST.json", manifest)
    print(
        "summary and manifest written",
        len(manifest["files"]),
        "files; synchronized",
        synchronized,
        "embedded audits; compacted",
        compacted,
        "optimizer records",
    )


if __name__ == "__main__":
    main()
