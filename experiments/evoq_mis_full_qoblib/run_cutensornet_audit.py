"""Cross-platform exact cuTensorNet audit for the frozen QAOA circuits.

Run ``export`` and ``decode`` with the Windows project environment. Run
``validate`` and ``sample`` inside the dedicated WSL cuQuantum environment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter

import numpy as np


HERE = Path(__file__).resolve().parent
AUDIT_DIR = HERE / "results" / "cutensornet"
CIRCUIT_DIR = AUDIT_DIR / "circuits"
METHODS = {
    "published_lr": [0.7, 0.4, 1.0, 1.0],
    "matched_random_search": [
        0.6424738670407446,
        0.7593921349176262,
        1.776791693083474,
        0.9917239502490107,
    ],
}
SMALL_CASES = ("es60fst03", "es60fst01")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def export_circuits() -> None:
    from qiskit import qpy
    from qiskit.quantum_info import Statevector
    import networkx as nx

    import run_cycle as rc

    CIRCUIT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for case_name in (*SMALL_CASES, "es60fst02"):
        case = rc.prepare_case(case_name)
        reduced = case.reduction.reduced_graph
        sorted_order = sorted(reduced.nodes())
        laplacian = nx.laplacian_matrix(reduced, nodelist=sorted_order).toarray()
        eigenvalues, eigenvectors = np.linalg.eigh(laplacian)
        nonzero = np.flatnonzero(eigenvalues > 1e-9)
        fiedler_index = int(nonzero[0]) if len(nonzero) else 0
        spectral_order = [
            sorted_order[i] for i in np.argsort(eigenvectors[:, fiedler_index])
        ]
        for ordering, node_order in (
            ("sorted", sorted_order),
            ("spectral", spectral_order),
        ):
          mapping = {node: i for i, node in enumerate(node_order)}
          relabeled = nx.relabel_nodes(reduced, mapping)
          hamiltonian = rc.mis_hamiltonian(relabeled, lambd=rc.LAMBDA)
          for method, genome in METHODS.items():
            betas, gammas = rc.schedule(np.asarray(genome, dtype=float))
            measured = rc.qaoa_mis(gammas, betas, hamiltonian, len(node_order))
            circuit = measured.remove_final_measurements(inplace=False)
            suffix = "" if ordering == "sorted" else "_spectral"
            qpy_path = CIRCUIT_DIR / f"{case_name}_{method}{suffix}.qpy"
            with qpy_path.open("wb") as handle:
                qpy.dump(circuit, handle)
            reference_path = None
            if case_name in SMALL_CASES:
                # Qiskit indexes amplitudes as q[n-1]...q[0]. cuTensorNet's
                # state tensor axes and sample strings are q[0]...q[n-1].
                state = Statevector.from_instruction(circuit).data
                q0_first = state.reshape((2,) * circuit.num_qubits).transpose(
                    tuple(reversed(range(circuit.num_qubits)))
                )
                reference_path = CIRCUIT_DIR / (
                    f"{case_name}_{method}{suffix}_reference.npz"
                )
                np.savez_compressed(reference_path, state=q0_first)
            rows.append(
                {
                    "case": case_name,
                    "method": method,
                    "ordering": ordering,
                    "qubit_node_order": [int(node) for node in node_order],
                    "genome": genome,
                    "qubits": circuit.num_qubits,
                    "depth": circuit.depth(),
                    "size": circuit.size(),
                    "operations": {str(k): int(v) for k, v in circuit.count_ops().items()},
                    "qpy": qpy_path.relative_to(HERE).as_posix(),
                    "qpy_sha256": sha256(qpy_path),
                    "reference": None
                    if reference_path is None
                    else reference_path.relative_to(HERE).as_posix(),
                    "reference_sha256": None
                    if reference_path is None
                    else sha256(reference_path),
                }
            )
    write_json(
        AUDIT_DIR / "export_manifest.json",
        {
            "created_at": rc.utc_now(),
            "qiskit": __import__("qiskit").__version__,
            "bitstring_order": "q0_to_qn_minus_1",
            "rows": rows,
        },
    )
    print(f"exported {len(rows)} circuits to {CIRCUIT_DIR}")


def load_circuit(case_name: str, method: str, ordering: str = "sorted"):
    from qiskit import qpy

    suffix = "" if ordering == "sorted" else "_spectral"
    path = CIRCUIT_DIR / f"{case_name}_{method}{suffix}.qpy"
    with path.open("rb") as handle:
        return qpy.load(handle)[0]


def cutensornet_provenance() -> dict:
    import cupy
    import cuquantum
    import qiskit

    props = cupy.cuda.runtime.getDeviceProperties(0)
    name = props["name"].decode() if isinstance(props["name"], bytes) else props["name"]
    return {
        "created_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "qiskit": qiskit.__version__,
        "cuquantum": cuquantum.__version__,
        "cupy": cupy.__version__,
        "gpu": name,
        "bitstring_order": "q0_to_qn_minus_1",
    }


def validate_small(hyper_samples: int) -> None:
    import cupy as cp
    from cuquantum.tensornet import NetworkOptions
    from cuquantum.tensornet.experimental import NetworkState, TNConfig

    rows = []
    for case_name in SMALL_CASES:
      for ordering in ("sorted", "spectral"):
        suffix = "" if ordering == "sorted" else "_spectral"
        for method in METHODS:
            circuit = load_circuit(case_name, method, ordering)
            reference_path = CIRCUIT_DIR / f"{case_name}_{method}{suffix}_reference.npz"
            reference = np.load(reference_path)["state"]
            start = perf_counter()
            with NetworkState.from_circuit(
                circuit,
                dtype="complex128",
                backend="cupy",
                config=TNConfig(num_hyper_samples=hyper_samples),
                options=NetworkOptions(device_id=0, memory_limit="85%"),
            ) as state:
                computed = cp.asnumpy(state.compute_state_vector())
            elapsed = perf_counter() - start
            overlap = np.vdot(reference.reshape(-1), computed.reshape(-1))
            fidelity = float(abs(overlap) ** 2)
            exact_p = abs(reference.reshape(-1)) ** 2
            computed_p = abs(computed.reshape(-1)) ** 2
            rows.append(
                {
                    "case": case_name,
                    "method": method,
                    "ordering": ordering,
                    "qubits": circuit.num_qubits,
                    "elapsed_seconds": elapsed,
                    "state_fidelity": fidelity,
                    "total_variation": float(0.5 * np.abs(exact_p - computed_p).sum()),
                    "max_probability_error": float(np.abs(exact_p - computed_p).max()),
                    "norm": float(computed_p.sum()),
                }
            )
            print(case_name, method, f"fidelity={fidelity:.12f}", f"sec={elapsed:.3f}")
    write_json(
        AUDIT_DIR / "small_exact_validation.json",
        {
            "stage": "cutensornet_small_exact_validation",
            "provenance": cutensornet_provenance(),
            "hyper_samples": hyper_samples,
            "rows": rows,
        },
    )


def sample_case(
    case_name: str,
    methods: list[str],
    shots: int,
    seed: int,
    hyper_samples: int,
    simulation_mode: str,
    bond: int,
    cutoff: float,
    ordering: str,
) -> None:
    from cuquantum.tensornet import NetworkOptions
    from cuquantum.tensornet.experimental import MPSConfig, NetworkState, TNConfig

    setting = (
        "exact"
        if simulation_mode == "exact"
        else f"mps_bond{bond}_cutoff{cutoff:.0e}".replace("+", "")
    )
    output_path = AUDIT_DIR / (
        f"raw_{case_name}_{ordering}_{setting}_{shots}shots.json"
    )
    config = (
        TNConfig(num_hyper_samples=hyper_samples)
        if simulation_mode == "exact"
        else MPSConfig(max_extent=bond, discarded_weight_cutoff=cutoff)
    )
    payload = {
        "stage": "cutensornet_sampling",
        "provenance": cutensornet_provenance(),
        "case": case_name,
        "shots": shots,
        "seed": seed,
        "ordering": ordering,
        "simulation_mode": simulation_mode,
        "bond": None if simulation_mode == "exact" else bond,
        "discarded_weight_cutoff": None if simulation_mode == "exact" else cutoff,
        "hyper_samples": hyper_samples,
        "rows": [],
    }
    if output_path.exists():
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    completed = {row["method"] for row in payload["rows"]}
    for offset, method in enumerate(methods):
        if method in completed:
            print(f"skip completed {method}")
            continue
        circuit = load_circuit(case_name, method, ordering)
        start = perf_counter()
        with NetworkState.from_circuit(
            circuit,
            dtype="complex128",
            backend="cupy",
            config=config,
            options=NetworkOptions(device_id=0, memory_limit="85%"),
        ) as state:
            counts = state.compute_sampling(shots, seed=seed + offset)
        elapsed = perf_counter() - start
        payload["rows"].append(
            {
                "method": method,
                "qubits": circuit.num_qubits,
                "depth": circuit.depth(),
                "size": circuit.size(),
                "elapsed_seconds": elapsed,
                "counts": {str(key): int(value) for key, value in counts.items()},
            }
        )
        write_json(output_path, payload)
        print(method, f"shots={shots}", f"unique={len(counts)}", f"sec={elapsed:.3f}")


def decode_samples(raw_path: Path) -> None:
    import run_cycle as rc

    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    case = rc.prepare_case(raw["case"])
    ordering = raw.get("ordering", "sorted")
    manifest = json.loads((AUDIT_DIR / "export_manifest.json").read_text())
    rows = []
    for row in raw["rows"]:
        counts = row["counts"]
        if ordering != "sorted":
            manifest_row = next(
                item
                for item in manifest["rows"]
                if item["case"] == raw["case"]
                and item["method"] == row["method"]
                and item["ordering"] == ordering
            )
            node_order = manifest_row["qubit_node_order"]
            sorted_nodes = sorted(node_order)
            position = {node: i for i, node in enumerate(node_order)}
            remapped = {}
            for bitstring, count in counts.items():
                decoded_order = "".join(bitstring[position[node]] for node in sorted_nodes)
                remapped[decoded_order] = remapped.get(decoded_order, 0) + count
            counts = remapped
        metrics = rc.summarize_counts(case, counts)
        rows.append({**{k: v for k, v in row.items() if k != "counts"}, "metrics": metrics})
        print(
            row["method"],
            f"BKS={metrics['bks_rate']:.4%}",
            f"near={metrics['near_bks_rate']:.4%}",
            f"feasible={metrics['feasible_rate']:.4%}",
        )
    write_json(
        HERE / "results" / "cutensornet_audit.json",
        {
            "stage": "decoded_cutensornet_exact_sampling",
            "source": raw_path.relative_to(HERE).as_posix(),
            "source_sha256": sha256(raw_path),
            "case": rc.case_metadata(case),
            "provenance": raw["provenance"],
            "shots": raw["shots"],
            "seed": raw["seed"],
            "ordering": ordering,
            "hyper_samples": raw["hyper_samples"],
            "rows": rows,
        },
    )


def parse_args():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("export")
    validate = sub.add_parser("validate")
    validate.add_argument("--hyper-samples", type=int, default=32)
    sample = sub.add_parser("sample")
    sample.add_argument("--case", default="es60fst02")
    sample.add_argument("--methods", nargs="+", choices=sorted(METHODS), default=list(METHODS))
    sample.add_argument("--shots", type=int, default=1_000)
    sample.add_argument("--seed", type=int, default=31_415_926)
    sample.add_argument("--hyper-samples", type=int, default=32)
    sample.add_argument("--simulation-mode", choices=("exact", "mps"), default="exact")
    sample.add_argument("--bond", type=int, default=64)
    sample.add_argument("--cutoff", type=float, default=1e-3)
    sample.add_argument("--ordering", choices=("sorted", "spectral"), default="sorted")
    decode = sub.add_parser("decode")
    decode.add_argument("raw_path", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "export":
        export_circuits()
    elif args.command == "validate":
        validate_small(args.hyper_samples)
    elif args.command == "sample":
        sample_case(
            args.case,
            args.methods,
            args.shots,
            args.seed,
            args.hyper_samples,
            args.simulation_mode,
            args.bond,
            args.cutoff,
            args.ordering,
        )
    else:
        decode_samples(args.raw_path.resolve())


if __name__ == "__main__":
    main()
