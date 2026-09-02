"""Create environment and SHA-256 manifests for the curvature artifact."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import networkx
import numpy
import scipy


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "experiments" / "aquila_configuration_curvature_phase0"
OUTPUT = ROOT / "results" / "aquila_configuration_curvature_phase0"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        commit = "unavailable"
    run_manifest = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "networkx": networkx.__version__,
        "git_commit_before_result_commit": commit,
        "qpu_tasks_submitted": 0,
    }
    (OUTPUT / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2) + "\n", encoding="utf-8")
    rows = []
    for directory in (EXPERIMENT, OUTPUT):
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.name != "artifact_manifest.json" and "__pycache__" not in path.parts:
                rows.append(
                    {
                        "path": path.relative_to(ROOT).as_posix(),
                        "bytes": path.stat().st_size,
                        "sha256": digest(path),
                    }
                )
    (OUTPUT / "artifact_manifest.json").write_text(
        json.dumps({"algorithm": "sha256", "files": rows}, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()

