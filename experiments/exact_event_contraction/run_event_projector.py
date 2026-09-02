"""Compile sparse Boolean events to exact MPOs and contract their probability."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from time import perf_counter

import numpy as np

from run_exact_event_contraction import (
    METHODS,
    ORDERINGS,
    REPO,
    RESULTS,
    SMALL_CASES,
    SUPPORT,
    atomic_json,
    exact_reference_probability,
    job_path,
    load_circuit,
    provenance,
    read_json,
    sha256,
    source_rows,
    support_case,
    to_complex,
    utc_now,
    optimizer_info,
)


def incidence_factorization(bitstrings: list[str], cut: int):
    """Return exact coordinates and a row basis for a prefix/suffix cut."""
    import sympy as sp

    support = set(bitstrings)
    prefixes = sorted({value[:cut] for value in bitstrings})
    suffixes = sorted({value[cut:] for value in bitstrings})
    prefix_index = {value: index for index, value in enumerate(prefixes)}
    suffix_index = {value: index for index, value in enumerate(suffixes)}
    matrix = sp.MutableSparseMatrix(len(prefixes), len(suffixes), {})
    for value in bitstrings:
        matrix[prefix_index[value[:cut]], suffix_index[value[cut:]]] = 1
    matrix = sp.ImmutableSparseMatrix(matrix)

    independent_rows = list(matrix.T.rref()[1])
    basis = matrix.extract(independent_rows, range(matrix.cols))
    independent_columns = list(basis.rref()[1])
    square = basis.extract(range(basis.rows), independent_columns)
    coordinates = matrix.extract(range(matrix.rows), independent_columns) * square.inv()
    if coordinates * basis != matrix:
        raise AssertionError(f"Exact incidence factorization failed at cut {cut}")
    return prefixes, [prefixes[index] for index in independent_rows], coordinates


def compile_indicator_tt(bitstrings: list[str]) -> list[np.ndarray]:
    """Compile an exact finite-language indicator into a minimal TT."""
    if not bitstrings or len(set(bitstrings)) != len(bitstrings):
        raise ValueError("Support must be non-empty and duplicate-free")
    qubits = len(bitstrings[0])
    if any(len(value) != qubits or set(value) - {"0", "1"} for value in bitstrings):
        raise ValueError("Support contains an invalid bitstring")

    cut_data = []
    for cut in range(qubits + 1):
        prefixes, basis_prefixes, coordinates = incidence_factorization(
            bitstrings, cut
        )
        cut_data.append(
            {
                "prefixes": prefixes,
                "prefix_index": {value: index for index, value in enumerate(prefixes)},
                "basis_prefixes": basis_prefixes,
                "coordinates": coordinates,
            }
        )

    cores: list[np.ndarray] = []
    for site in range(qubits):
        left_basis = cut_data[site]["basis_prefixes"]
        right = cut_data[site + 1]
        core = np.zeros((len(left_basis), 2, len(right["basis_prefixes"])))
        for left_index, prefix in enumerate(left_basis):
            for bit in (0, 1):
                extended = prefix + str(bit)
                row = right["prefix_index"].get(extended)
                if row is None:
                    continue
                for right_index, value in enumerate(right["coordinates"].row(row)):
                    core[left_index, bit, right_index] = float(value)
        cores.append(core)

    if cores[0].shape[0] != 1 or cores[-1].shape[-1] != 1:
        raise AssertionError("TT boundary ranks are not one")
    return cores


def evaluate_tt(cores: list[np.ndarray], bitstring: str) -> complex:
    value = np.ones((1,), dtype=np.complex128)
    for core, bit in zip(cores, bitstring, strict=True):
        value = value @ core[:, int(bit), :]
    return complex(value.item())


def deterministic_outsiders(
    qubits: int, support: set[str], target: int = 4096
) -> list[str]:
    domain_size = 1 << qubits
    wanted = min(target, domain_size - len(support))
    if domain_size <= target + len(support):
        return [
            format(value, f"0{qubits}b")
            for value in range(domain_size)
            if format(value, f"0{qubits}b") not in support
        ]
    rng = np.random.default_rng(260902)
    output: set[str] = set()
    while len(output) < wanted:
        batch = rng.integers(0, 2, size=(wanted, qubits), dtype=np.int8)
        for row in batch:
            value = "".join(str(int(bit)) for bit in row)
            if value not in support:
                output.add(value)
            if len(output) == wanted:
                break
    return sorted(output)


def diagonal_mpo(cores: list[np.ndarray]) -> list[np.ndarray]:
    output = []
    last = len(cores) - 1
    for site, core in enumerate(cores):
        left_rank, _, right_rank = core.shape
        if site == 0 and site == last:
            tensor = np.zeros((2, 2), dtype=np.complex128)
            for bit in (0, 1):
                tensor[bit, bit] = core[0, bit, 0]
        elif site == 0:
            tensor = np.zeros((2, right_rank, 2), dtype=np.complex128)
            for bit in (0, 1):
                tensor[bit, :, bit] = core[0, bit, :]
        elif site == last:
            tensor = np.zeros((left_rank, 2, 2), dtype=np.complex128)
            for bit in (0, 1):
                tensor[:, bit, bit] = core[:, bit, 0]
        else:
            tensor = np.zeros(
                (left_rank, 2, right_rank, 2), dtype=np.complex128
            )
            for bit in (0, 1):
                tensor[:, bit, :, bit] = core[:, bit, :]
        output.append(tensor)
    return output


def tt_archive_path(case_name: str, ordering: str):
    return RESULTS / f"event_tt_{case_name}_{ordering}.npz"


def save_tt(path, cores: list[np.ndarray]) -> None:
    temporary = path.with_suffix(".tmp.npz")
    np.savez_compressed(
        temporary, **{f"core_{index:03d}": core for index, core in enumerate(cores)}
    )
    temporary.replace(path)


def load_tt(path) -> list[np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        return [np.asarray(archive[key]) for key in sorted(archive.files)]


def compile_and_audit(case_name: str, ordering: str) -> tuple[list[np.ndarray], dict]:
    report_path = RESULTS / f"mpo_audit_{case_name}_{ordering}.json"
    archive_path = tt_archive_path(case_name, ordering)
    if report_path.exists() and archive_path.exists():
        report = read_json(report_path)
        if (
            report.get("schema_version") == 2
            and report.get("support_sha256") == sha256(SUPPORT)
            and report.get("tt_archive_sha256") == sha256(archive_path)
            and report.get("passed")
        ):
            return load_tt(archive_path), report

    support = support_case(case_name)
    bitstrings = support["orderings"][ordering]["bitstrings_q0_first"]
    started = perf_counter()
    cores = compile_indicator_tt(bitstrings)
    compile_seconds = perf_counter() - started
    members = [abs(evaluate_tt(cores, value) - 1.0) for value in bitstrings]
    outsiders = deterministic_outsiders(len(bitstrings[0]), set(bitstrings))
    nonmembers = [abs(evaluate_tt(cores, value)) for value in outsiders]
    ranks = [cores[0].shape[0]] + [core.shape[-1] for core in cores]
    mpo = diagonal_mpo(cores)
    report = {
        "schema_version": 2,
        "stage": "exact_event_mpo_representation_audit",
        "created_at": utc_now(),
        "case": case_name,
        "ordering": ordering,
        "qubits": len(bitstrings[0]),
        "support_size": len(bitstrings),
        "support_sha256": sha256(SUPPORT),
        "bond_ranks": ranks,
        "max_bond_rank": max(ranks),
        "tt_dense_entries": int(sum(core.size for core in cores)),
        "tt_nonzero_entries": int(sum(np.count_nonzero(core) for core in cores)),
        "coefficient_values": sorted(
            {float(value) for core in cores for value in np.unique(core)}
        ),
        "all_coefficients_integral": bool(
            all(np.array_equal(core, np.rint(core)) for core in cores)
        ),
        "mpo_dense_entries": int(sum(tensor.size for tensor in mpo)),
        "mpo_bytes_complex128": int(sum(tensor.nbytes for tensor in mpo)),
        "member_checks": len(members),
        "nonmember_checks": len(nonmembers),
        "max_member_absolute_error": float(max(members, default=0.0)),
        "max_nonmember_absolute_error": float(max(nonmembers, default=0.0)),
        "compile_seconds": compile_seconds,
    }
    report["passed"] = (
        report["max_member_absolute_error"] <= 1e-10
        and report["max_nonmember_absolute_error"] <= 1e-10
    )
    if not report["passed"]:
        raise AssertionError(report)
    save_tt(archive_path, cores)
    report["tt_archive"] = archive_path.relative_to(REPO).as_posix()
    report["tt_archive_sha256"] = sha256(archive_path)
    atomic_json(report_path, report)
    return cores, report


def exact_event_expectation(
    case_name: str,
    method: str,
    ordering: str,
    hyper_samples: int,
    mode: str,
    layers: int | None = None,
) -> dict:
    import cupy as cp
    from cuquantum.tensornet import NetworkOptions
    from cuquantum.tensornet.experimental import NetworkOperator, NetworkState, TNConfig

    rows = source_rows()
    row = rows[(case_name, method, ordering)]
    circuit, circuit_path = load_circuit(row)
    parent_circuit_sha256 = semantic_circuit_sha256(circuit)
    if layers is not None:
        circuit = truncate_qaoa_layers(circuit, layers)
    cores, audit = compile_and_audit(case_name, ordering)
    tensors = diagonal_mpo(cores)
    output = mpo_job_path(case_name, method, ordering, mode, layers)
    payload = {
        "stage": "exact_event_mpo_expectation",
        "mode": mode,
        "case": case_name,
        "method": method,
        "ordering": ordering,
        "qubits": int(circuit.num_qubits),
        "event_support_size": audit["support_size"],
        "circuit": circuit_path.relative_to(REPO).as_posix(),
        "circuit_sha256": row["qpy_sha256"],
        "parent_semantic_circuit_sha256": parent_circuit_sha256,
        "contracted_semantic_circuit_sha256": semantic_circuit_sha256(circuit),
        "qaoa_layers": layers if layers is not None else 15,
        "support_sha256": sha256(SUPPORT),
        "hyper_samples": hyper_samples,
        "bond_ranks": audit["bond_ranks"],
        "max_bond_rank": audit["max_bond_rank"],
        "mpo_bytes_complex128": audit["mpo_bytes_complex128"],
        "representation_audit": audit,
        "provenance": provenance(hyper_samples),
        "complete": False,
    }
    atomic_json(output, payload)
    options = NetworkOptions(device_id=0, memory_limit="85%")
    operator = NetworkOperator(
        [2] * circuit.num_qubits, dtype="complex128", options=options
    )
    cleanup_error = None
    try:
        operator.append_mpo(1.0, list(range(circuit.num_qubits)), tensors)
        started = perf_counter()
        state = NetworkState.from_circuit(
            circuit,
            dtype="complex128",
            backend="cupy",
            config=TNConfig(num_hyper_samples=hyper_samples),
            options=options,
        )
        try:
            expectation, norm = state.compute_expectation(
                operator, return_norm=True, release_workspace=True
            )
        except Exception as primary_error:
            try:
                state.free()
            except Exception as error:
                cleanup_error = error
            raise primary_error
        else:
            state.free()
        elapsed = perf_counter() - started
        expectation = to_complex(expectation)
        norm = to_complex(norm)
        payload.update(
            {
                "expectation_real": expectation.real,
                "expectation_imag": expectation.imag,
                "norm_real": norm.real,
                "norm_imag": norm.imag,
                "elapsed_seconds": elapsed,
                "complete": True,
                "completed_at": utc_now(),
            }
        )
        cp.get_default_memory_pool().free_all_blocks()
    except Exception as error:
        payload.update(
            {
                "error_type": type(error).__name__,
                "error": str(error),
                "failed_at": utc_now(),
            }
        )
        if cleanup_error is not None:
            payload.update(
                {
                    "cleanup_error_type": type(cleanup_error).__name__,
                    "cleanup_error": str(cleanup_error),
                }
            )
        atomic_json(output, payload)
        raise
    atomic_json(output, payload)
    print(
        f"[{case_name}/{method}/{ordering}] p={expectation.real:.12g} "
        f"norm={norm.real:.12g} sec={elapsed:.3f}",
        flush=True,
    )
    return payload


def density_mpo_interleaved(circuit, mpo_tensors):
    """Return a public interleaved einsum specification for <psi|MPO|psi>."""
    import cupy as cp
    from cuquantum.tensornet import CircuitToEinsum

    expression, operands = CircuitToEinsum(
        circuit, dtype="complex128", backend="cupy"
    ).density_matrix()
    input_expression, output_expression = expression.split("->")
    input_terms = input_expression.split(",")
    if len(input_terms) != len(operands):
        raise AssertionError("Density-matrix expression/operand mismatch")
    if len(output_expression) != 2 * circuit.num_qubits:
        raise AssertionError("Unexpected density-matrix output mode count")

    label_map: dict[str, int] = {}

    def mode(label: str) -> int:
        if label not in label_map:
            label_map[label] = len(label_map)
        return label_map[label]

    interleaved = []
    for operand, term in zip(operands, input_terms, strict=True):
        interleaved.extend((operand, [mode(label) for label in term]))
    ket_modes = [mode(label) for label in output_expression[: circuit.num_qubits]]
    bra_modes = [mode(label) for label in output_expression[circuit.num_qubits :]]
    next_mode = len(label_map)
    bonds = list(range(next_mode, next_mode + circuit.num_qubits - 1))
    for site, tensor in enumerate(mpo_tensors):
        if circuit.num_qubits == 1:
            modes = [ket_modes[site], bra_modes[site]]
        elif site == 0:
            modes = [ket_modes[site], bonds[site], bra_modes[site]]
        elif site == circuit.num_qubits - 1:
            modes = [bonds[site - 1], ket_modes[site], bra_modes[site]]
        else:
            modes = [
                bonds[site - 1],
                ket_modes[site],
                bonds[site],
                bra_modes[site],
            ]
        interleaved.extend((cp.asarray(tensor), modes))
    interleaved.append([])
    return interleaved, {
        "circuit_operand_count": len(operands),
        "mpo_operand_count": len(mpo_tensors),
        "total_operand_count": len(operands) + len(mpo_tensors),
        "density_open_modes": len(output_expression),
    }


def truncate_qaoa_layers(circuit, layers: int):
    """Retain the first complete QAOA layers from a bound exported circuit."""
    if not 1 <= layers <= 15:
        raise ValueError("layers must be in [1, 15]")
    edges = {
        tuple(
            sorted(circuit.find_bit(qubit).index for qubit in instruction.qubits)
        )
        for instruction in circuit.data
        if instruction.operation.name == "rzz"
    }
    incident = {
        qubit: {edge for edge in edges if qubit in edge}
        for qubit in range(circuit.num_qubits)
    }
    output = circuit.copy_empty_like()
    output_qubits = {
        qubit: output.qubits[index] for index, qubit in enumerate(circuit.qubits)
    }
    output_clbits = {
        clbit: output.clbits[index] for index, clbit in enumerate(circuit.clbits)
    }
    mixer_counts = [0] * circuit.num_qubits
    phase_counts = [0] * circuit.num_qubits
    hadamard_counts = [0] * circuit.num_qubits
    edge_counts = {edge: 0 for edge in edges}
    for instruction in circuit.data:
        name = instruction.operation.name
        qubits = [circuit.find_bit(qubit).index for qubit in instruction.qubits]
        if name == "h":
            qubit = qubits[0]
            if mixer_counts[qubit] != 0 or hadamard_counts[qubit] != 0:
                raise AssertionError("Initial H is missing or duplicated")
            hadamard_counts[qubit] += 1
            output.append(
                instruction.operation,
                [output_qubits[qubit] for qubit in instruction.qubits],
                [output_clbits[clbit] for clbit in instruction.clbits],
            )
            continue
        if name not in {"rz", "rzz", "rx"}:
            raise AssertionError(f"Unexpected operation in QAOA circuit: {name}")
        stages = {mixer_counts[index] for index in qubits}
        if len(stages) != 1:
            raise AssertionError(f"Layer mismatch for {name} on qubits {qubits}")
        stage = stages.pop()
        if not all(hadamard_counts[index] == 1 for index in qubits):
            raise AssertionError(f"{name} encountered before initial H")
        if name == "rz":
            qubit = qubits[0]
            if phase_counts[qubit] != stage:
                raise AssertionError(f"Duplicate or missing RZ on qubit {qubit}")
            phase_counts[qubit] += 1
        elif name == "rzz":
            edge = tuple(sorted(qubits))
            if not all(phase_counts[index] == stage + 1 for index in qubits):
                raise AssertionError(f"RZZ on {edge} encountered before layer RZ")
            if edge_counts[edge] != stage:
                raise AssertionError(f"Duplicate or missing RZZ on edge {edge}")
            edge_counts[edge] += 1
        else:
            qubit = qubits[0]
            if phase_counts[qubit] != stage + 1 or any(
                edge_counts[edge] != stage + 1 for edge in incident[qubit]
            ):
                raise AssertionError(f"RX on qubit {qubit} before cost layer closed")
        if stage < layers:
            output.append(
                instruction.operation,
                [output_qubits[qubit] for qubit in instruction.qubits],
                [output_clbits[clbit] for clbit in instruction.clbits],
            )
        if name == "rx":
            mixer_counts[qubits[0]] += 1

    if (
        set(mixer_counts) != {15}
        or set(phase_counts) != {15}
        or set(hadamard_counts) != {1}
        or set(edge_counts.values()) != {15}
    ):
        raise AssertionError("The source circuit does not contain 15 complete layers")
    counts = output.count_ops()
    full_counts = circuit.count_ops()
    expected = {
        "h": circuit.num_qubits,
        "rz": circuit.num_qubits * layers,
        "rzz": (full_counts.get("rzz", 0) // 15) * layers,
        "rx": circuit.num_qubits * layers,
    }
    for name, count in expected.items():
        if counts.get(name, 0) != count:
            raise AssertionError((name, counts.get(name, 0), count))
    return output


def semantic_circuit_sha256(circuit) -> str:
    rows = []
    for instruction in circuit.data:
        params = []
        for value in instruction.operation.params:
            try:
                params.append(float(value))
            except (TypeError, ValueError):
                params.append(str(value))
        rows.append(
            {
                "name": instruction.operation.name,
                "qubits": [
                    circuit.find_bit(qubit).index for qubit in instruction.qubits
                ],
                "params": params,
            }
        )
    encoded = json.dumps(
        {"qubits": circuit.num_qubits, "instructions": rows},
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def topology_circuit_sha256(circuit) -> str:
    rows = [
        {
            "name": instruction.operation.name,
            "qubits": [circuit.find_bit(qubit).index for qubit in instruction.qubits],
            "shape": [2] * (2 * len(instruction.qubits)),
        }
        for instruction in circuit.data
    ]
    encoded = json.dumps(
        {"qubits": circuit.num_qubits, "instructions": rows},
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def compact_optimizer_info(info) -> dict:
    full = optimizer_info(info)
    full["path_length"] = len(full.get("path", ()))
    full["intermediate_count"] = len(full.get("intermediate_modes", ()))
    full.pop("repr", None)
    full.pop("path", None)
    full.pop("intermediate_modes", None)
    return full


def mpo_job_path(
    case_name: str,
    method: str,
    ordering: str,
    mode: str,
    layers: int | None,
):
    if layers is None:
        return job_path(case_name, method, ordering, mode)
    return RESULTS / f"{mode}_p{layers:02d}_{case_name}_{method}_{ordering}.json"


def lowlevel_event_expectation(
    case_name: str,
    method: str,
    ordering: str,
    hyper_samples: int,
    mode: str,
    layers: int | None = None,
    max_slices: int = 65_536,
    max_opt_cost: float = 1e13,
) -> dict:
    """Contract the density network and event MPO through the low-level API."""
    import cupy as cp
    from cuquantum.tensornet import Network, NetworkOptions, OptimizerOptions

    rows = source_rows()
    row = rows[(case_name, method, ordering)]
    circuit, circuit_path = load_circuit(row)
    parent_circuit_sha256 = semantic_circuit_sha256(circuit)
    if layers is not None:
        circuit = truncate_qaoa_layers(circuit, layers)
    cores, audit = compile_and_audit(case_name, ordering)
    interleaved, network_shape = density_mpo_interleaved(
        circuit, diagonal_mpo(cores)
    )
    output = mpo_job_path(case_name, method, ordering, mode, layers)
    payload = {
        "stage": "exact_event_lowlevel_density_mpo",
        "mode": mode,
        "case": case_name,
        "method": method,
        "ordering": ordering,
        "qubits": int(circuit.num_qubits),
        "event_support_size": audit["support_size"],
        "circuit": circuit_path.relative_to(REPO).as_posix(),
        "circuit_sha256": row["qpy_sha256"],
        "parent_semantic_circuit_sha256": parent_circuit_sha256,
        "contracted_semantic_circuit_sha256": semantic_circuit_sha256(circuit),
        "qaoa_layers": layers if layers is not None else 15,
        "execution_guard": {
            "max_slices": max_slices,
            "max_opt_cost": max_opt_cost,
        },
        "support_sha256": sha256(SUPPORT),
        "hyper_samples": hyper_samples,
        "bond_ranks": audit["bond_ranks"],
        "max_bond_rank": audit["max_bond_rank"],
        "mpo_bytes_complex128": audit["mpo_bytes_complex128"],
        "network_shape": network_shape,
        "representation_audit": audit,
        "provenance": provenance(hyper_samples),
        "complete": False,
    }
    atomic_json(output, payload)
    options = NetworkOptions(device_id=0, memory_limit="85%")
    optimize = OptimizerOptions(samples=hyper_samples, seed=260902)
    try:
        with Network(*interleaved, options=options) as network:
            started = perf_counter()
            _, path_info = network.contract_path(optimize=optimize)
            payload["path_seconds"] = perf_counter() - started
            payload["path_info"] = compact_optimizer_info(path_info)
            atomic_json(output, payload)
            if (
                int(path_info.num_slices) > max_slices
                or float(path_info.opt_cost) > max_opt_cost
            ):
                payload.update(
                    {
                        "resource_rejected": True,
                        "rejection_reason": (
                            "optimized path exceeds the frozen slice/cost guard"
                        ),
                        "completed_at": utc_now(),
                    }
                )
                atomic_json(output, payload)
                print(
                    f"[{case_name}/{method}/{ordering}] path rejected: "
                    f"slices={int(path_info.num_slices)} "
                    f"cost={float(path_info.opt_cost):.6g}",
                    flush=True,
                )
                return payload
            started = perf_counter()
            expectation = to_complex(network.contract(release_workspace=True))
            payload["contraction_seconds"] = perf_counter() - started
        payload.update(
            {
                "expectation_real": expectation.real,
                "expectation_imag": expectation.imag,
                "complete": True,
                "completed_at": utc_now(),
            }
        )
        cp.get_default_memory_pool().free_all_blocks()
    except Exception as error:
        payload.update(
            {
                "error_type": type(error).__name__,
                "error": str(error),
                "failed_at": utc_now(),
            }
        )
        atomic_json(output, payload)
        raise
    atomic_json(output, payload)
    print(
        f"[{case_name}/{method}/{ordering}] p={expectation.real:.12g} "
        f"path={payload['path_seconds']:.3f}s "
        f"contract={payload['contraction_seconds']:.3f}s",
        flush=True,
    )
    return payload


def representation_audit_all() -> None:
    rows = []
    for case_name in (*SMALL_CASES, "es60fst02"):
        for ordering in ORDERINGS:
            _, report = compile_and_audit(case_name, ordering)
            rows.append(report)
            print(
                f"[{case_name}/{ordering}] rank={report['max_bond_rank']} "
                f"entries={report['tt_dense_entries']} sec={report['compile_seconds']:.3f}",
                flush=True,
            )
    atomic_json(
        RESULTS / "mpo_representation_audit_summary.json",
        {
            "stage": "exact_event_mpo_representation_audit_summary",
            "created_at": utc_now(),
            "rows": rows,
            "complete": all(row["passed"] for row in rows),
        },
    )


def self_test(hyper_samples: int) -> None:
    rows = []
    for case_name, method, ordering in itertools.product(
        SMALL_CASES, METHODS, ORDERINGS
    ):
        payload = exact_event_expectation(
            case_name, method, ordering, hyper_samples, "mpo_selftest"
        )
        reference = exact_reference_probability(case_name, method, ordering)
        error = abs(payload["expectation_real"] - reference)
        row = {
            "case": case_name,
            "method": method,
            "ordering": ordering,
            "computed_probability": payload["expectation_real"],
            "reference_probability": reference,
            "absolute_error": error,
            "imaginary_absolute": abs(payload["expectation_imag"]),
            "norm_absolute_error": abs(payload["norm_real"] - 1.0),
        }
        row["passed"] = (
            error <= 1e-10
            and row["imaginary_absolute"] <= 1e-10
            and row["norm_absolute_error"] <= 1e-10
        )
        rows.append(row)
    result = {
        "stage": "exact_event_mpo_self_test",
        "created_at": utc_now(),
        "tolerance": 1e-10,
        "rows": rows,
        "max_absolute_error": max(row["absolute_error"] for row in rows),
        "complete": all(row["passed"] for row in rows),
    }
    atomic_json(RESULTS / "mpo_self_test_summary.json", result)
    if not result["complete"]:
        raise AssertionError(result)
    print("MPO self-test passed", result["max_absolute_error"])


def lowlevel_self_test(hyper_samples: int) -> None:
    rows = []
    for case_name, method, ordering in itertools.product(
        SMALL_CASES, METHODS, ORDERINGS
    ):
        payload = lowlevel_event_expectation(
            case_name, method, ordering, hyper_samples, "lowlevel_mpo_selftest"
        )
        reference = exact_reference_probability(case_name, method, ordering)
        error = abs(payload["expectation_real"] - reference)
        row = {
            "case": case_name,
            "method": method,
            "ordering": ordering,
            "computed_probability": payload["expectation_real"],
            "reference_probability": reference,
            "absolute_error": error,
            "imaginary_absolute": abs(payload["expectation_imag"]),
        }
        row["passed"] = error <= 1e-10 and row["imaginary_absolute"] <= 1e-10
        rows.append(row)
    result = {
        "stage": "exact_event_lowlevel_density_mpo_self_test",
        "created_at": utc_now(),
        "tolerance": 1e-10,
        "rows": rows,
        "max_absolute_error": max(row["absolute_error"] for row in rows),
        "complete": all(row["passed"] for row in rows),
    }
    atomic_json(RESULTS / "lowlevel_mpo_self_test_summary.json", result)
    if not result["complete"]:
        raise AssertionError(result)
    print("low-level MPO self-test passed", result["max_absolute_error"])


def validate_layer_extraction() -> None:
    rows = []
    for (case_name, method, ordering), source_row in source_rows().items():
        circuit, _ = load_circuit(source_row)
        if case_name not in (*SMALL_CASES, "es60fst02"):
            continue
        parent_hash = semantic_circuit_sha256(circuit)
        for layers in (1, 2, 4, 8, 15):
            truncated = truncate_qaoa_layers(circuit, layers)
            row = {
                "case": case_name,
                "method": method,
                "ordering": ordering,
                "qaoa_layers": layers,
                "operations": dict(truncated.count_ops()),
                "semantic_circuit_sha256": semantic_circuit_sha256(truncated),
                "topology_circuit_sha256": topology_circuit_sha256(truncated),
            }
            if layers == 15 and row["semantic_circuit_sha256"] != parent_hash:
                raise AssertionError((case_name, method, ordering, "p15 mismatch"))
            rows.append(row)
    topology_groups: dict[tuple[str, str, int], set[str]] = {}
    for row in rows:
        key = (row["case"], row["ordering"], row["qaoa_layers"])
        topology_groups.setdefault(key, set()).add(row["topology_circuit_sha256"])
    if any(len(hashes) != 1 for hashes in topology_groups.values()):
        raise AssertionError("Schedule circuit topologies differ")
    result = {
        "stage": "qaoa_layer_extraction_validation",
        "created_at": utc_now(),
        "depths": [1, 2, 4, 8, 15],
        "rows": rows,
        "schedule_topology_groups": len(topology_groups),
        "all_schedule_topologies_match": True,
        "complete": True,
    }
    atomic_json(RESULTS / "layer_extraction_validation.json", result)
    print("layer extraction validated", len(rows), "rows")


def dense_event_probability(circuit, bitstrings: list[str]) -> float:
    from qiskit.quantum_info import Statevector

    state = Statevector.from_instruction(circuit).data
    return float(
        sum(abs(state[int(bitstring[::-1], 2)]) ** 2 for bitstring in bitstrings)
    )


def depth_self_test(hyper_samples: int) -> None:
    rows = []
    for case_name, method, ordering, layers in itertools.product(
        SMALL_CASES, METHODS, ORDERINGS, (1, 2, 4, 8, 15)
    ):
        payload = lowlevel_event_expectation(
            case_name,
            method,
            ordering,
            hyper_samples,
            "depth_mpo_selftest",
            layers,
        )
        source_row = source_rows()[(case_name, method, ordering)]
        full_circuit, _ = load_circuit(source_row)
        circuit = truncate_qaoa_layers(full_circuit, layers)
        bitstrings = support_case(case_name)["orderings"][ordering][
            "bitstrings_q0_first"
        ]
        reference = dense_event_probability(circuit, bitstrings)
        error = abs(payload["expectation_real"] - reference)
        row = {
            "case": case_name,
            "method": method,
            "ordering": ordering,
            "qaoa_layers": layers,
            "computed_probability": payload["expectation_real"],
            "reference_probability": reference,
            "absolute_error": error,
            "imaginary_absolute": abs(payload["expectation_imag"]),
        }
        row["passed"] = error <= 1e-10 and row["imaginary_absolute"] <= 1e-10
        rows.append(row)
    result = {
        "stage": "exact_event_depth_sweep_self_test",
        "created_at": utc_now(),
        "depths": [1, 2, 4, 8, 15],
        "tolerance": 1e-10,
        "rows": rows,
        "max_absolute_error": max(row["absolute_error"] for row in rows),
        "complete": all(row["passed"] for row in rows),
    }
    atomic_json(RESULTS / "depth_sweep_self_test_summary.json", result)
    if not result["complete"]:
        raise AssertionError(result)
    print("depth-sweep self-test passed", result["max_absolute_error"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=(
            "audit",
            "self-test",
            "pilot",
            "run",
            "lowlevel-self-test",
            "lowlevel-pilot",
            "lowlevel-run",
            "validate-layers",
            "depth-self-test",
        ),
    )
    parser.add_argument("--case", default="es60fst02")
    parser.add_argument("--method", choices=METHODS, default="published_lr")
    parser.add_argument("--ordering", choices=ORDERINGS, default="spectral")
    parser.add_argument("--hyper-samples", type=int, default=32)
    parser.add_argument("--layers", type=int)
    parser.add_argument("--max-slices", type=int, default=65_536)
    parser.add_argument("--max-opt-cost", type=float, default=1e13)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.action == "audit":
        representation_audit_all()
    elif args.action == "self-test":
        self_test(args.hyper_samples)
    elif args.action == "lowlevel-self-test":
        lowlevel_self_test(args.hyper_samples)
    elif args.action == "validate-layers":
        validate_layer_extraction()
    elif args.action == "depth-self-test":
        depth_self_test(args.hyper_samples)
    elif args.action in ("lowlevel-pilot", "lowlevel-run"):
        lowlevel_event_expectation(
            args.case,
            args.method,
            args.ordering,
            args.hyper_samples,
            "lowlevel_mpo_pilot"
            if args.action == "lowlevel-pilot"
            else "lowlevel_mpo_full",
            args.layers,
            args.max_slices,
            args.max_opt_cost,
        )
    else:
        exact_event_expectation(
            args.case,
            args.method,
            args.ordering,
            args.hyper_samples,
            "mpo_pilot" if args.action == "pilot" else "mpo_full",
            args.layers,
        )


if __name__ == "__main__":
    main()
