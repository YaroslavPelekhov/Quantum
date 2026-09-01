"""Build a comprehensive deterministic manifest for the completed CBRK cycle."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import matplotlib
import networkx
import numpy
import scipy


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "causal_boundary_response_phase0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    result_files = sorted(path for path in OUT.iterdir() if path.is_file() and path.name != "manifest.json")
    source_files = sorted(path for path in EXPERIMENT.iterdir() if path.is_file() and path.name != "__init__.py")
    manifest = {
        "experiment": "causal boundary-response kernelization Phase 0 and falsification",
        "verdict": "FALSIFIED_BY_CONTROLLED_BOUNDARY_HISTORIES",
        "commands": [
            "python -m experiments.causal_boundary_response_phase0.run_phase0",
            "python -m experiments.causal_boundary_response_phase0.run_rank_audit",
            "python -m experiments.causal_boundary_response_phase0.run_physical_surrogate",
            "python -m experiments.causal_boundary_response_phase0.run_capacity_audit",
            "python -m experiments.causal_boundary_response_phase0.run_host_transfer",
            "python -m experiments.causal_boundary_response_phase0.run_process_gram",
            "python -m unittest experiments.causal_boundary_response_phase0.test_phase0 -v",
        ],
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "networkx": networkx.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "result_sha256": {path.name: sha256(path) for path in result_files},
        "source_sha256": {path.name: sha256(path) for path in source_files},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

