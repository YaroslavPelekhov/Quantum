"""Hash reproducibility artifacts, excluding temporary renders and build logs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXCLUDED_PARTS = {"__pycache__", "tmp"}
EXCLUDED_SUFFIXES = {".aux", ".log", ".out"}


def main():
    rows = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.suffix in EXCLUDED_SUFFIXES or path.name == "artifact_manifest.json":
            continue
        data = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    payload = {"root": ".", "artifact_count": len(rows), "artifacts": rows}
    (ROOT / "artifact_manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(rows)} artifacts")


if __name__ == "__main__":
    main()
