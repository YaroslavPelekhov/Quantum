from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import qiskit
import qiskit_aer
import scipy


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def git_revision(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


artifact_paths = list(HERE.glob("results*/*.json"))
artifact_paths.extend([
    HERE / "NOVELTY_AUDIT.md",
    HERE / "EXTERNAL_BASELINE_AUDIT.md",
    HERE / "RESEARCH_CYCLE_REPORT.md",
    HERE / "paper" / "main.tex",
    HERE / "paper" / "references.bib",
    HERE / "paper" / "generated" / "paper_summary.json",
    HERE / "paper" / "output" / "pdf" / "gsn_qaoa_mis_manuscript.pdf",
])

artifacts = []
for path in sorted(path for path in artifact_paths if path.exists()):
    payload = path.read_bytes()
    artifacts.append({
        "path": str(path.relative_to(ROOT)),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    })

manifest = {
    "generated_by": str(Path(__file__).resolve()),
    "environment": {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__,
    },
    "repositories": {
        "QOBLIB": git_revision(ROOT / "QOBLIB"),
        "metriq-gym": git_revision(ROOT / "metriq-gym"),
        "QAOA-Parameter-Transfer-via-GAT": git_revision(ROOT / "baselines" / "QAOA-Parameter-Transfer-via-GAT"),
    },
    "artifacts": artifacts,
}
(HERE / "ARTIFACT_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"artifacts": len(artifacts), "manifest": str(HERE / "ARTIFACT_MANIFEST.json")}, indent=2))
