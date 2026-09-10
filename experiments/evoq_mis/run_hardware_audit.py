from __future__ import annotations

import gc
import json
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import transpile
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import CouplingMap
from qiskit_aer import AerSimulator

from qaoa_mis import counts_metrics, enumerate_exact_space, qaoa_circuit
from run_scaleup_audit import build_scale_graphs
from run_multitask_normalized import summarize


EXPERIMENT_DIR = Path(__file__).resolve().parent
SOURCE_PATH = EXPERIMENT_DIR / "results_multitask_normalized" / "results.json"
OUTPUT_DIR = EXPERIMENT_DIR / "results_hardware_audit"


def circuit_metrics(circuit) -> dict:
    operations = {str(key): int(value) for key, value in circuit.count_ops().items()}
    two_qubit = sum(
        1 for instruction in circuit.data
        if getattr(instruction.operation, "num_qubits", 0) == 2
    )
    return {
        "qubits": circuit.num_qubits,
        "classical_bits": circuit.num_clbits,
        "depth": int(circuit.depth()),
        "size": int(circuit.size()),
        "two_qubit_operations": int(two_qubit),
        "operations": operations,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    params = np.asarray(source["champion"]["params"], dtype=float)
    graphs = build_scale_graphs()
    topologies = {
        "line": lambda n: CouplingMap.from_line(n),
        "grid_5x5": lambda n: CouplingMap.from_grid(5, 5),
        "hexagonal_lattice_30": lambda n: CouplingMap.from_hexagonal_lattice(3, 3),
    }
    report = {
        "experiment": "Hardware-aware routing and synthetic calibrated-noise audit",
        "schedule_source": str(SOURCE_PATH.resolve()),
        "params": params.tolist(),
        "resource_audit": {},
        "analytical_error_proxy": {},
        "limitations": [
            "GenericBackendV2 generates synthetic backend properties; this is not a named QPU calibration.",
            "Hardware-routed noisy MPS was attempted at 128 and 16 shots but did not finish the first 20-qubit case within a practical CPU budget.",
            "The no-error survival proxy assumes independent errors and is not a substitute for density-matrix, trajectory or QPU data.",
        ],
    }
    started = time.perf_counter()

    for graph in graphs:
        original = qaoa_circuit(graph, params, p=2, measure=True, cost_scale="max_coefficient")
        baseline = transpile(original, basis_gates=["id", "rz", "sx", "x", "cx"], optimization_level=0, seed_transpiler=20260803)
        graph_resources = {"unconstrained_basis": circuit_metrics(baseline)}
        for name, factory in topologies.items():
            coupling = factory(graph.n)
            compiled = transpile(
                original,
                basis_gates=["id", "rz", "sx", "x", "cx"],
                coupling_map=coupling,
                optimization_level=0,
                seed_transpiler=20260803,
                layout_method="trivial",
                routing_method="basic",
            )
            graph_resources[name] = circuit_metrics(compiled)
            print(json.dumps({"resource_topology_complete": graph.name, "topology": name}), flush=True)
        report["resource_audit"][graph.name] = graph_resources
        print(json.dumps({"resource_complete": graph.name}), flush=True)

    (OUTPUT_DIR / "resource_checkpoint.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    error_rates = {"one_qubit": 0.001, "two_qubit": 0.01, "measurement": 0.02}
    for graph in graphs:
        graph_proxy = {}
        for topology, metrics in report["resource_audit"][graph.name].items():
            operations = metrics["operations"]
            one_qubit = sum(operations.get(name, 0) for name in ("id", "rz", "sx", "x"))
            two_qubit = int(metrics["two_qubit_operations"])
            measurements = int(operations.get("measure", graph.n))
            survival = (
                (1.0 - error_rates["one_qubit"]) ** one_qubit
                * (1.0 - error_rates["two_qubit"]) ** two_qubit
                * (1.0 - error_rates["measurement"]) ** measurements
            )
            graph_proxy[topology] = {
                "one_qubit_operations": one_qubit,
                "two_qubit_operations": two_qubit,
                "measurements": measurements,
                "independent_no_error_survival_proxy": survival,
            }
        report["analytical_error_proxy"][graph.name] = graph_proxy

    report["seconds"] = time.perf_counter() - started
    report["promotion_gate"] = {
        "checks": {
            "all_topologies_transpile": all(len(row) == 4 for row in report["resource_audit"].values()),
            "error_proxy_complete": len(report["analytical_error_proxy"]) == len(graphs),
            "hardware_routed_noisy_sampling_feasible_on_cpu": False,
        }
    }
    report["promotion_gate"]["promote_to_confirmatory_cycle"] = False
    (OUTPUT_DIR / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    graph_names = [graph.name for graph in graphs]
    topology_names = ["unconstrained_basis", "line", "grid_5x5", "hexagonal_lattice_30"]
    x = np.arange(len(graph_names))
    width = 0.2
    plt.figure(figsize=(9.2, 5.2))
    for index, topology in enumerate(topology_names):
        cx = [report["resource_audit"][graph][topology]["operations"].get("cx", 0) for graph in graph_names]
        plt.bar(x + (index - 1.5) * width, cx, width, label=topology)
    plt.xticks(x, graph_names)
    plt.ylabel("CX count after transpilation")
    plt.title("Routing overhead for frozen normalized QAOA schedule")
    plt.grid(axis="y", alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "routing_cx_counts.png", dpi=180)
    plt.close()

    print(json.dumps({
        "seconds": report["seconds"],
        "promotion_gate": report["promotion_gate"],
        "results": str((OUTPUT_DIR / "results.json").resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()
