"""Build a SHA-256 inventory for the Phase-0 experiment and results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "experiments" / "hardware_model_witness_phase0"
RESULTS = ROOT / "results" / "hardware_model_witness_phase0"
OUTPUT = RESULTS / "artifact_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    files = []
    for directory in (EXPERIMENT, RESULTS):
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path == OUTPUT or "__pycache__" in path.parts:
                continue
            files.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    payload = {
        "schema_version": 1,
        "root": ".",
        "file_count": len(files),
        "files": files,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
