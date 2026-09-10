from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import networkx as nx
import numpy as np
from qiskit_aer import AerSimulator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "metriq-gym"))
from metriq_gym.circuits import qaoa_circuit  # noqa: E402


OUTPUT_DIR = Path(__file__).resolve().parent / "results_metriq_lrqaoa"


def cut_cost(bits: str, graph: nx.Graph) -> float:
    return float(sum(data["weight"] for u, v, data in graph.edges(data=True) if bits[u] != bits[v]))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config = {
        "benchmark_name": "Linear Ramp QAOA",
        "graph_type": "1D",
        "num_qubits": 10,
        "qaoa_layers": [3, 5, 7, 10],
        "delta_beta": 0.3,
        "delta_gamma": 0.3,
        "shots": 4096,
        "trials": 1,
        "seed": 20260803,
        "execution": "Direct use of metriq_gym.circuits.qaoa_circuit on local Qiskit Aer",
    }
    rng = random.Random(config["seed"])
    graph = nx.Graph()
    graph.add_nodes_from(range(config["num_qubits"]))
    weights = [0.1, 0.2, 0.3, 0.5, 1.0]
    graph.add_weighted_edges_from((i, i + 1, rng.choice(weights)) for i in range(config["num_qubits"] - 1))

    all_bits = [format(mask, f"0{config['num_qubits']}b") for mask in range(1 << config["num_qubits"])]
    costs = np.asarray([cut_cost(bits, graph) for bits in all_bits], dtype=float)
    optimum = float(costs.max())
    simulator = AerSimulator()
    results = []
    for layers in config["qaoa_layers"]:
        circuit = qaoa_circuit(graph, layers, "1D", "Direct")
        ramp = list(range(1, layers + 1))
        betas = [i * config["delta_beta"] / layers for i in reversed(ramp)]
        gammas = [i * config["delta_gamma"] / layers for i in ramp]
        bound = circuit.assign_parameters(betas + gammas)
        counts = simulator.run(bound, shots=config["shots"], seed_simulator=config["seed"] + layers).result().get_counts()
        total_cost = sum(count * cut_cost(bits.replace(" ", ""), graph) for bits, count in counts.items())
        optimal_counts = sum(count for bits, count in counts.items() if abs(cut_cost(bits.replace(" ", ""), graph) - optimum) < 1e-12)
        results.append({
            "layers": layers,
            "approx_ratio": total_cost / (optimum * config["shots"]),
            "optimal_probability": optimal_counts / config["shots"],
            "circuit_depth": int(bound.depth()),
            "two_qubit_gates": int(sum(1 for item in bound.data if item.operation.num_qubits == 2)),
        })

    uniform_expected = float(costs.mean() / optimum)
    report = {
        "params": config,
        "platform": {"provider": "local", "device": "aer_simulator", "simulator": True},
        "instance": {
            "weighted_edges": [[u, v, data["weight"]] for u, v, data in graph.edges(data=True)],
            "exact_maxcut": optimum,
            "uniform_random_approx_ratio": uniform_expected,
        },
        "results": results,
        "score": max(row["approx_ratio"] for row in results),
    }
    (OUTPUT_DIR / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
