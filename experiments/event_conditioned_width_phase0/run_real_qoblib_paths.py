"""Compare exact event representations on the frozen 55-qubit QOBLIB circuit.

This runner performs path search only.  It deliberately uses the same
cuTensorNet optimizer budget for every representation and never contracts a
path, so it is safe to use as the first representation-level falsification
screen.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EXACT = REPO / "experiments" / "exact_event_contraction"
RESULTS = REPO / "results" / "event_conditioned_width_phase0"
sys.path.insert(0, str(EXACT))

import run_event_projector as event_projector  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, default=json_default) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def json_default(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def circuit_edges(circuit) -> list[tuple[int, int]]:
    """Extract the logical MIS edges from any retained QAOA prefix."""
    edges = {
        tuple(
            sorted(circuit.find_bit(qubit).index for qubit in instruction.qubits)
        )
        for instruction in circuit.data
        if instruction.operation.name == "rzz"
    }
    return sorted(edges)


def count_states(qubits: int, target: int, cut: int) -> list[int]:
    """Reachable prefix counts that can still finish at ``target``."""
    low = max(0, target - (qubits - cut))
    high = min(cut, target)
    return list(range(low, high + 1))


def cardinality_factors(qubits: int, target: int) -> list[np.ndarray]:
    """Exact, zero-pruned one-hot automaton for sum(x_i) == target."""
    if not 0 <= target <= qubits:
        raise ValueError("target cardinality is outside [0, qubits]")
    if qubits == 1:
        return [np.asarray([target == 0, target == 1], dtype=np.complex128)]

    output: list[np.ndarray] = []
    for site in range(qubits):
        left = count_states(qubits, target, site)
        right = count_states(qubits, target, site + 1)
        left_index = {value: index for index, value in enumerate(left)}
        right_index = {value: index for index, value in enumerate(right)}
        core = np.zeros((len(left), 2, len(right)), dtype=np.complex128)
        for count in left:
            for bit in (0, 1):
                next_count = count + bit
                if next_count in right_index:
                    core[left_index[count], bit, right_index[next_count]] = 1
        if site == 0:
            core = core[0, :, :]
        elif site == qubits - 1:
            core = core[:, :, 0]
        output.append(core)
    return output


def density_local_mis_interleaved(circuit, target: int):
    """Build rho(z,z) times local independence and cardinality factors."""
    import cupy as cp
    from cuquantum.tensornet import CircuitToEinsum

    expression, operands = CircuitToEinsum(
        circuit, dtype="complex128", backend="cupy"
    ).density_matrix()
    input_expression, output_expression = expression.split("->")
    terms = input_expression.split(",")
    if len(terms) != len(operands):
        raise AssertionError("Density-matrix expression/operand mismatch")
    if len(output_expression) != 2 * circuit.num_qubits:
        raise AssertionError("Unexpected density-matrix output mode count")

    label_map: dict[str, int] = {}

    def mode(label: str) -> int:
        if label not in label_map:
            label_map[label] = len(label_map)
        return label_map[label]

    interleaved: list = []
    for operand, term in zip(operands, terms, strict=True):
        interleaved.extend((operand, [mode(label) for label in term]))
    ket_modes = [mode(label) for label in output_expression[: circuit.num_qubits]]
    bra_modes = [mode(label) for label in output_expression[circuit.num_qubits :]]

    equality = cp.eye(2, dtype=cp.complex128)
    independent = cp.asarray([[1, 1], [1, 0]], dtype=cp.complex128)
    for ket_mode, bra_mode in zip(ket_modes, bra_modes, strict=True):
        interleaved.extend((equality, [ket_mode, bra_mode]))
    for left, right in circuit_edges(circuit):
        interleaved.extend((independent, [ket_modes[left], ket_modes[right]]))

    next_mode = len(label_map)
    counter_modes = list(
        range(next_mode, next_mode + max(0, circuit.num_qubits - 1))
    )
    for site, factor in enumerate(cardinality_factors(circuit.num_qubits, target)):
        if circuit.num_qubits == 1:
            modes = [ket_modes[site]]
        elif site == 0:
            modes = [ket_modes[site], counter_modes[site]]
        elif site == circuit.num_qubits - 1:
            modes = [counter_modes[site - 1], ket_modes[site]]
        else:
            modes = [counter_modes[site - 1], ket_modes[site], counter_modes[site]]
        interleaved.extend((cp.asarray(factor), modes))
    interleaved.append([])
    return interleaved, {
        "encoding": "local_mis_plus_pruned_cardinality",
        "edge_factor_count": len(circuit_edges(circuit)),
        "equality_factor_count": circuit.num_qubits,
        "cardinality_factor_count": circuit.num_qubits,
        "max_cardinality_bond": max(
            len(count_states(circuit.num_qubits, target, cut))
            for cut in range(circuit.num_qubits + 1)
        ),
        "total_operand_count": len(interleaved) // 2,
    }


def path_record(interleaved, samples: int, seed: int) -> dict:
    from cuquantum.tensornet import Network, NetworkOptions, OptimizerOptions

    options = NetworkOptions(device_id=0, memory_limit="85%")
    optimize = OptimizerOptions(samples=samples, seed=seed)
    started = perf_counter()
    with Network(*interleaved, options=options) as network:
        _, info = network.contract_path(optimize=optimize)
    elapsed = perf_counter() - started
    compact = event_projector.compact_optimizer_info(info)
    compact["path_search_seconds"] = elapsed
    return compact


def run(
    case_name: str,
    method: str,
    orderings: list[str],
    layers: list[int],
    representations: list[str],
    samples: int,
    seed: int,
) -> dict:
    source = event_projector.source_rows()
    support = event_projector.support_case(case_name)
    output_path = RESULTS / "real_qoblib_representation_paths.json"
    requested = {
        (case_name, method, ordering, depth, representation)
        for ordering in orderings
        for depth in layers
        for representation in representations
    }
    rows = []
    if output_path.exists():
        previous = json.loads(output_path.read_text(encoding="utf-8"))
        rows = [
            row
            for row in previous.get("rows", [])
            if (
                row.get("case"),
                row.get("method"),
                row.get("ordering"),
                row.get("qaoa_layers"),
                row.get("representation"),
            )
            not in requested
        ]
    for ordering in orderings:
        source_row = source[(case_name, method, ordering)]
        parent, circuit_path = event_projector.load_circuit(source_row)
        for depth in layers:
            circuit = event_projector.truncate_qaoa_layers(parent, depth)
            for representation in representations:
                started = perf_counter()
                if representation == "minimal_mpo":
                    cores, audit = event_projector.compile_and_audit(
                        case_name, ordering
                    )
                    interleaved, shape = event_projector.density_mpo_interleaved(
                        circuit, event_projector.diagonal_mpo(cores)
                    )
                    encoding = {
                        "encoding": "fixed_order_rank_minimal_mpo",
                        "max_event_bond": audit["max_bond_rank"],
                        **shape,
                    }
                elif representation == "local_mis":
                    interleaved, encoding = density_local_mis_interleaved(
                        circuit, int(support["independence_number"])
                    )
                else:
                    raise ValueError(f"Unknown representation: {representation}")
                build_seconds = perf_counter() - started
                row = {
                    "case": case_name,
                    "method": method,
                    "ordering": ordering,
                    "qaoa_layers": depth,
                    "representation": representation,
                    "qubits": circuit.num_qubits,
                    "circuit_operations": len(circuit.data),
                    "circuit": circuit_path.relative_to(REPO).as_posix(),
                    "event_support_size": support["support_size"],
                    "event_build_seconds": build_seconds,
                    "encoding": encoding,
                }
                try:
                    row.update(path_record(interleaved, samples, seed))
                    row["path_complete"] = True
                except Exception as error:  # keep every failed path as evidence
                    row.update(
                        {
                            "path_complete": False,
                            "error_type": type(error).__name__,
                            "error": str(error),
                        }
                    )
                rows.append(row)
                atomic_json(
                    output_path,
                    {
                        "stage": "event_conditioned_width_real_path_screen",
                        "created_at": utc_now(),
                        "path_search_only": True,
                        "optimizer": {"samples": samples, "seed": seed},
                        "rows": rows,
                    },
                )
                print(
                    case_name,
                    ordering,
                    f"p={depth}",
                    representation,
                    row.get("opt_cost", row.get("error_type")),
                    flush=True,
                )
    return {"rows": rows}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default="es60fst02")
    parser.add_argument("--method", default="published_lr")
    parser.add_argument("--orderings", nargs="+", default=["spectral", "sorted"])
    parser.add_argument("--layers", nargs="+", type=int, default=[1, 2, 3, 4])
    parser.add_argument(
        "--representations",
        nargs="+",
        default=["minimal_mpo", "local_mis"],
        choices=["minimal_mpo", "local_mis"],
    )
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=260902)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run(
        case_name=arguments.case,
        method=arguments.method,
        orderings=arguments.orderings,
        layers=arguments.layers,
        representations=arguments.representations,
        samples=arguments.samples,
        seed=arguments.seed,
    )
