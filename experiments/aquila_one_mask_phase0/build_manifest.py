"""Build environment and SHA-256 manifests for the Phase-0 artifact."""

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
import torch


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "experiments" / "aquila_one_mask_phase0"
OUTPUT = ROOT / "results" / "aquila_one_mask_phase0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "git_commit_before_result_commit": commit,
        "qpu_tasks_submitted": 0,
    }
    (OUTPUT / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2) + "\n", encoding="utf-8")
    files = []
    for directory in (EXPERIMENT, OUTPUT):
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.name != "artifact_manifest.json" and "__pycache__" not in path.parts:
                files.append(
                    {
                        "path": path.relative_to(ROOT).as_posix(),
                        "bytes": path.stat().st_size,
                        "sha256": sha256(path),
                    }
                )
    payload = {"algorithm": "sha256", "files": files}
    (OUTPUT / "artifact_manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

