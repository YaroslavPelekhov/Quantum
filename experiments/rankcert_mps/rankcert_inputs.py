"""Read-only reconstruction and validation of the frozen RankCert inputs."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PROJECT = REPO / "experiments" / "evoq_mis_full_qoblib"
RESULTS = REPO / "results" / "rankcert_mps"
CROSS_MANIFEST = PROJECT / "results" / "cross_case_replication" / "export_manifest.json"
AVES_MANIFEST = PROJECT / "results" / "independent_ladder" / "export_manifest.json"
EXTERNAL_EXACT = PROJECT / "results" / "external_validity" / "exact_statevector.json"
AVES_EXACT = PROJECT / "results" / "mps_ladder" / "exact_references.json"
AVES_PRIOR_MPS = PROJECT / "results" / "mps_ladder" / "mps_ladder.json"
CROSS_PRIOR_MPS = PROJECT / "results" / "cross_case_replication" / "aer_jobs.json"
INPUT_VALIDATION = RESULTS / "input_validation.json"

CASES = ("karate", "chesapeake", "football", "ibm32", "aves-sparrow-social")
METHODS = ("published_lr", "prior_matched_random")
SCHEDULE_NAMES = {"published_lr": "LR", "prior_matched_random": "MR"}
ORDERINGS = ("sorted", "spectral")
SETTINGS = (
    {"name": "released", "bond": 64, "cutoff": 1e-3},
    {"name": "confirm", "bond": 128, "cutoff": 1e-4},
    {"name": "bond128", "bond": 128, "cutoff": 1e-12},
    {"name": "cutoff1e-4", "bond": 1024, "cutoff": 1e-4},
    {"name": "cutoff1e-5", "bond": 1024, "cutoff": 1e-5},
)
ROUNDED_EFFECTS = {
    "karate": 0.086412,
    "chesapeake": -0.134214,
    "football": 0.019269,
    "ibm32": -0.246123,
    "aves-sparrow-social": -0.012139,
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def resolve_project_file(relative: str, expected_hash: str) -> Path:
    """Resolve an immutable artifact, including the intentionally unstaged 24q arrays."""
    candidates = [
        PROJECT / relative,
        REPO.parent / "experiments" / "evoq_mis_full_qoblib" / relative,
    ]
    existing = [candidate for candidate in candidates if candidate.exists()]
    if not existing:
        raise FileNotFoundError(f"Frozen artifact is absent: {relative}; tried {candidates}")
    # Hashing is done in validate_inputs. Here we only avoid silently choosing an
    # alternate cache whose manifest identity is unknown.
    return existing[0]


def _exact_genomes() -> dict[tuple[str, str, str], list[float]]:
    payload = read_json(EXTERNAL_EXACT)
    result = {}
    for row in payload["rows"]:
        if row["method"] in METHODS:
            result[(row["case"], row["method"], row["ordering"])] = row["genome"]
    aves_payload = read_json(PROJECT / "results" / "exact_extension" / "aves_exact.json")
    for row in aves_payload["rows"]:
        if row["method"] in METHODS:
            result[(row["case"], row["method"], row["ordering"])] = row["genome"]
    return result


def load_specs() -> list[dict]:
    cross = read_json(CROSS_MANIFEST)
    aves = read_json(AVES_MANIFEST)
    genomes = _exact_genomes()
    rows = []
    for source_name, manifest in (("cross_case_replication", cross), ("independent_ladder", aves)):
        for row in manifest["rows"]:
            if row["case"] not in CASES or row["method"] not in METHODS:
                continue
            circuit = resolve_project_file(row["circuit_file"], row["circuit_sha256"])
            reference = resolve_project_file(row["reference_file"], row["reference_sha256"])
            key = (row["case"], row["method"], row["ordering"])
            rows.append({
                "case": row["case"],
                "qubits": int(row["qubits"]),
                "depth": int(row["depth"]),
                "method": row["method"],
                "schedule": SCHEDULE_NAMES[row["method"]],
                "schedule_parameters": genomes[key],
                "ordering": row["ordering"],
                "circuit_file": str(circuit),
                "circuit_sha256": row["circuit_sha256"],
                "reference_file": str(reference),
                "reference_sha256": row["reference_sha256"],
                "exact_metrics": row["exact_metrics"],
                "scorer": row["scorer"],
                "source_manifest": str(CROSS_MANIFEST if source_name == "cross_case_replication" else AVES_MANIFEST),
                "source_manifest_kind": source_name,
            })
    rows.sort(key=lambda row: (CASES.index(row["case"]), METHODS.index(row["method"]), ORDERINGS.index(row["ordering"])))
    expected = len(CASES) * len(METHODS) * len(ORDERINGS)
    if len(rows) != expected:
        raise AssertionError(f"Expected {expected} frozen LR/MR circuit definitions, found {len(rows)}")
    return rows


def exact_effects(specs: list[dict]) -> list[dict]:
    indexed = {(row["case"], row["method"], row["ordering"]): row for row in specs}
    effects = []
    for case in CASES:
        values = []
        for ordering in ORDERINGS:
            lr = indexed[(case, "published_lr", ordering)]["exact_metrics"]["bks_rate"]
            mr = indexed[(case, "prior_matched_random", ordering)]["exact_metrics"]["bks_rate"]
            delta = float(mr) - float(lr)
            values.append(delta)
            effects.append({
                "case": case,
                "ordering": ordering,
                "p_bks_exact_lr": lr,
                "p_bks_exact_mr": mr,
                "exact_delta": delta,
                "rounded_target": ROUNDED_EFFECTS[case],
                "rounded_agreement": abs(delta - ROUNDED_EFFECTS[case]) <= 5e-7,
            })
        if abs(values[0] - values[1]) > 1e-12:
            raise AssertionError(f"Exact effect depends on ordering for {case}: {values}")
        if not all(row["rounded_agreement"] for row in effects if row["case"] == case):
            raise AssertionError(f"Exact effect disagrees with frozen rounded target for {case}")
    return effects


def validate_inputs(hash_references: bool = True) -> dict:
    specs = load_specs()
    file_checks = []
    for row in specs:
        for kind in ("circuit", "reference"):
            path = Path(row[f"{kind}_file"])
            actual = sha256(path) if kind == "circuit" or hash_references else None
            expected = row[f"{kind}_sha256"]
            file_checks.append({
                "case": row["case"], "method": row["method"], "ordering": row["ordering"],
                "kind": kind, "path": str(path), "bytes": path.stat().st_size,
                "expected_sha256": expected, "actual_sha256": actual,
                "valid": actual == expected if actual is not None else None,
            })
    failures = [row for row in file_checks if row["valid"] is False]
    if failures:
        raise RuntimeError(f"Frozen artifact hash failures: {failures}")
    effects = exact_effects(specs)
    payload = {
        "stage": "rankcert_frozen_input_validation",
        "complete": hash_references,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "immutable_inputs_only": True,
        "manifests": [
            {"path": str(path), "sha256": sha256(path)}
            for path in (CROSS_MANIFEST, AVES_MANIFEST, EXTERNAL_EXACT, AVES_EXACT, AVES_PRIOR_MPS, CROSS_PRIOR_MPS)
        ],
        "settings": list(SETTINGS),
        "effects": effects,
        "files": file_checks,
    }
    atomic_json(INPUT_VALIDATION, payload)
    return payload


def lookup_spec(case: str, method: str, ordering: str) -> dict:
    for row in load_specs():
        if (row["case"], row["method"], row["ordering"]) == (case, method, ordering):
            return row
    raise KeyError((case, method, ordering))


if __name__ == "__main__":
    result = validate_inputs(hash_references=True)
    print(json.dumps({"output": str(INPUT_VALIDATION), "effects": result["effects"], "files": len(result["files"])}, indent=2))
