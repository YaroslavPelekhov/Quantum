"""Build and audit the exact BKS support for frozen QOBLIB kernels."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = REPO / "experiments" / "evoq_mis_full_qoblib"
RESULTS = REPO / "results" / "exact_event_contraction"
MANIFEST = SOURCE / "results" / "cutensornet" / "export_manifest.json"
OUTPUT = RESULTS / "event_support.json"
CASES = ("es60fst03", "es60fst01", "es60fst02")
EXPECTED = {
    "es60fst03": {"qubits": 12, "edges": 16, "bks": 55},
    "es60fst01": {"qubits": 15, "edges": 21, "bks": 60},
    "es60fst02": {
        "qubits": 55,
        "edges": 91,
        "alpha": 23,
        "support_size": 384,
        "bks": 88,
    },
}

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def enumerate_maximum_independent_sets(graph: nx.Graph) -> tuple[int, list[tuple]]:
    """Return the independence number and every maximum independent set."""
    largest = -1
    winners: list[tuple] = []
    for clique in nx.find_cliques(nx.complement(graph)):
        size = len(clique)
        ordered = tuple(sorted(clique))
        if size > largest:
            largest = size
            winners = [ordered]
        elif size == largest:
            winners.append(ordered)
    return largest, sorted(set(winners))


def manifest_rows() -> dict[tuple[str, str], dict]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = {}
    for row in payload["rows"]:
        if row["case"] in CASES:
            rows[(row["case"], row["ordering"])] = row
    missing = [
        (case, ordering)
        for case in CASES
        for ordering in ("sorted", "spectral")
        if (case, ordering) not in rows
    ]
    if missing:
        raise RuntimeError(f"Missing export-manifest rows: {missing}")
    return rows


def build_case(case_name: str, rows: dict[tuple[str, str], dict]) -> dict:
    sys.path.insert(0, str(SOURCE))
    import run_cycle as rc

    case = rc.prepare_case(case_name)
    reduced = case.reduction.reduced_graph
    expected = EXPECTED[case_name]
    if reduced.number_of_nodes() != expected["qubits"]:
        raise AssertionError((case_name, "qubits", reduced.number_of_nodes()))
    if reduced.number_of_edges() != expected["edges"]:
        raise AssertionError((case_name, "edges", reduced.number_of_edges()))

    alpha, node_sets = enumerate_maximum_independent_sets(reduced)
    decoded_sizes = set()
    sorted_nodes = sorted(reduced.nodes())
    sorted_support = []
    for selected_tuple in node_sets:
        selected = set(selected_tuple)
        bitstring = "".join("1" if node in selected else "0" for node in sorted_nodes)
        decoded = case.decoder.decode(bitstring)
        if not decoded.raw_feasible:
            raise AssertionError((case_name, "infeasible support string", bitstring))
        decoded_sizes.add(int(decoded.raw_selected))
        if int(decoded.raw_selected) != expected["bks"]:
            raise AssertionError(
                (case_name, "non-BKS maximum set", decoded.raw_selected, bitstring)
            )
        sorted_support.append((selected_tuple, bitstring))

    order_payload = {}
    for ordering in ("sorted", "spectral"):
        node_order = rows[(case_name, ordering)]["qubit_node_order"]
        if set(node_order) != set(sorted_nodes):
            raise AssertionError((case_name, ordering, "node-order mismatch"))
        bitstrings = []
        for selected_tuple, _ in sorted_support:
            selected = set(selected_tuple)
            bitstrings.append(
                "".join("1" if node in selected else "0" for node in node_order)
            )
        if len(bitstrings) != len(set(bitstrings)):
            raise AssertionError((case_name, ordering, "duplicate support strings"))
        order_payload[ordering] = {
            "node_order": node_order,
            "bitstrings_q0_first": sorted(bitstrings),
        }

    if case_name == "es60fst02":
        if alpha != expected["alpha"]:
            raise AssertionError((case_name, "alpha", alpha))
        if len(node_sets) != expected["support_size"]:
            raise AssertionError((case_name, "support size", len(node_sets)))

    return {
        "case": case_name,
        "qubits": reduced.number_of_nodes(),
        "edges": reduced.number_of_edges(),
        "independence_number": alpha,
        "support_size": len(node_sets),
        "decoded_sizes": sorted(decoded_sizes),
        "bks": expected["bks"],
        "orderings": order_payload,
    }


def main() -> None:
    rows = manifest_rows()
    payload = {
        "stage": "exact_event_support",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "networkx": nx.__version__,
        "source_manifest": MANIFEST.relative_to(REPO).as_posix(),
        "source_manifest_sha256": sha256(MANIFEST),
        "qoblib_solutions_commit": rc.git_commit(rc.BASELINE_REPO),
        "bitstring_convention": "q0_to_qn_minus_1",
        "cases": [build_case(case_name, rows) for case_name in CASES],
    }
    atomic_json(OUTPUT, payload)
    print(
        "built",
        OUTPUT,
        [(row["case"], row["support_size"]) for row in payload["cases"]],
    )


if __name__ == "__main__":
    main()
