"""Write the immutable RankCert-MPS environment and repository audit."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import psutil
import scipy


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "rankcert_mps"

# Captured read-only before this namespace was created on 2026-08-17.
INITIAL_GIT_STATE = {
    "commit": "506c4f2504311fb854365d3917877a72227043e5",
    "branch": "main",
    "upstream": "origin/main",
    "ahead": 0,
    "behind": 0,
    "dirty_entries": [
        {
            "path": "baselines/qoblib-solutions",
            "porcelain_v2": (
                "1 .M S.MU 160000 160000 160000 "
                "bd3e8a6d36b48b07d53dc605b020d4cb35da2147 "
                "bd3e8a6d36b48b07d53dc605b020d4cb35da2147 "
                "baselines/qoblib-solutions"
            ),
            "note": "pre-existing dirty submodule working tree; not modified",
        }
    ],
    "untracked_entries": [],
}


def run(command: list[str]) -> dict:
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, errors="replace", check=False
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except OSError as exc:
        return {"command": command, "returncode": None, "stdout": "", "stderr": str(exc)}


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def cpu_model() -> str:
    result = run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)",
        ]
    )
    return result["stdout"] or platform.processor()


def main() -> None:
    import qiskit
    import qiskit_aer
    from qiskit_aer import AerSimulator

    smi = run(["nvidia-smi"])
    smi_query = run(
        [
            "nvidia-smi",
            "--query-gpu=name,driver_version,memory.total",
            "--format=csv,noheader,nounits",
        ]
    )
    query_parts = [part.strip() for part in smi_query["stdout"].split(",")]
    cuda = run(["nvcc", "--version"])
    cutn = run(
        [
            "wsl.exe",
            "-d",
            "Ubuntu",
            "--",
            "/root/.venvs/evoq-cuquantum/bin/python",
            "-c",
            (
                "import importlib.metadata as m, json; "
                "names=['cuquantum-python','cuquantum','cupy-cuda12x']; "
                "print(json.dumps({n:(m.version(n) if any(d.metadata['Name'].lower()==n.lower() "
                "for d in m.distributions()) else None) for n in names}))"
            ),
        ]
    )
    virtual = psutil.virtual_memory()
    simulator = AerSimulator()
    payload = {
        "stage": "rankcert_mps_environment_audit",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "repository": {
            "path": str(REPO),
            "initial_state_before_modification": INITIAL_GIT_STATE,
            "current_commit": run(["git", "-C", str(REPO), "rev-parse", "HEAD"])["stdout"],
            "current_branch": run(["git", "-C", str(REPO), "branch", "--show-current"])["stdout"],
            "current_status_porcelain_v2": run(
                ["git", "-C", str(REPO), "status", "--porcelain=v2", "--branch"]
            )["stdout"].splitlines(),
        },
        "host": {
            "os": platform.platform(),
            "cpu_model": cpu_model(),
            "logical_cpu_count": psutil.cpu_count(logical=True),
            "physical_cpu_count": psutil.cpu_count(logical=False),
            "ram_total_bytes": virtual.total,
            "ram_total_gib": virtual.total / (1024**3),
            "ram_available_at_audit_bytes": virtual.available,
            "ram_available_at_audit_gib": virtual.available / (1024**3),
        },
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "qiskit": qiskit.__version__,
            "qiskit_aer": qiskit_aer.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "psutil": psutil.__version__,
        },
        "aer": {
            "available_methods": list(simulator.available_methods()),
            "available_devices": list(simulator.available_devices()),
        },
        "gpu": {
            "model": query_parts[0] if len(query_parts) >= 1 else None,
            "driver_version": query_parts[1] if len(query_parts) >= 2 else None,
            "vram_mib": float(query_parts[2]) if len(query_parts) >= 3 else None,
            "nvidia_smi_returncode": smi["returncode"],
            "nvcc": cuda,
        },
        "cutensornet_wsl": cutn,
        "constraints": {
            "remote_compute_forbidden": True,
            "aer_mps_gpu_available": "GPU" in simulator.available_devices(),
            "preexisting_low_memory_cause": "Telegram.exe working set approximately 24.9 GiB",
        },
    }
    atomic_write(RESULTS / "environment.json", json.dumps(payload, indent=2) + "\n")
    atomic_write(
        RESULTS / "nvidia-smi.txt",
        f"command: nvidia-smi\nreturncode: {smi['returncode']}\n\n{smi['stdout']}\n{smi['stderr']}\n",
    )
    print(json.dumps({
        "environment": str(RESULTS / "environment.json"),
        "nvidia_smi": str(RESULTS / "nvidia-smi.txt"),
        "ram_available_gib": payload["host"]["ram_available_at_audit_gib"],
        "aer_devices": payload["aer"]["available_devices"],
    }, indent=2))


if __name__ == "__main__":
    main()
