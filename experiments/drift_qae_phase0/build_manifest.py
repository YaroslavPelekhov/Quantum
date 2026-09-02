"""Build the deterministic artifact manifest for drift-QAE Phase 0."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path

import matplotlib
import numpy
import scipy


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "drift_qae_phase0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def git_value(*arguments: str) -> str:
    return subprocess.check_output(["git", *arguments], cwd=ROOT, text=True).strip()


def main() -> None:
    result_files = sorted(
        path for path in OUT.iterdir() if path.is_file() and path.name != "artifact_manifest.json"
    )
    source_files = sorted(
        path for path in EXPERIMENT.iterdir() if path.is_file() and path.name != "__init__.py"
    )
    manifest = {
        "experiment": "drift-aware amplitude estimation Phase 0",
        "verdict": "KILL_BROAD_DRIFT_ASTAR",
        "git_head_before_artifact_commit": git_value("rev-parse", "HEAD"),
        "git_branch": git_value("branch", "--show-current"),
        "commands": [
            "python -m unittest experiments.drift_qae_phase0.test_phase0 -v",
            "python -m experiments.drift_qae_phase0.run_phase0",
            "python -m experiments.drift_qae_phase0.run_strong_estimator_audit",
            "python -m experiments.drift_qae_phase0.plot_results",
            "python -m experiments.drift_qae_phase0.build_manifest",
        ],
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "hardware_queries": 0,
        "qpu_observations": 0,
        "result_sha256": {path.name: sha256(path) for path in result_files},
        "source_sha256": {path.name: sha256(path) for path in source_files},
    }
    (OUT / "artifact_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

