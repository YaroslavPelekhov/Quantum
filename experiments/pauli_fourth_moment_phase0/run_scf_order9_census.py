"""Exhaustively screen McKay's connected order-nine graph census for SCF."""

from __future__ import annotations

import ast
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

import networkx as nx

from run_scf_hbar_falsification import has_claw, is_line_graph, simplicial_cliques


CENSUS_URL = "https://users.cecs.anu.edu.au/~bdm/data/graph9c.g6"
CENSUS_SHA256 = "ad4fda3b6c7157e6711270cdc9cefdc06ac5154d7bd6ce295e1ac41808755c65"
IMPERFECT_COMMIT = "467eb611c09631fcf310da8dc73c35cb3b8fe098"
IMPERFECT_URL = (
    "https://raw.githubusercontent.com/wangjie212/BetaNumber/"
    f"{IMPERFECT_COMMIT}/src/seesaw-shadow-tomography/data/test9.txt"
)
IMPERFECT_SHA256 = "1eb261786d59004f6373b54016ca55c88a36b6f2bdb01edbe538d71b2f69ede7"


def fetch_verified(url: str, expected: str) -> bytes:
    with urllib.request.urlopen(url) as response:
        payload = response.read()
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise AssertionError(f"hash mismatch for {url}: {actual}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    census_payload = fetch_verified(CENSUS_URL, CENSUS_SHA256)
    imperfect_payload = fetch_verified(IMPERFECT_URL, IMPERFECT_SHA256)
    imperfect = {
        ast.literal_eval(line)[0]
        for line in imperfect_payload.decode("utf-8").splitlines()
        if line.strip()
    }
    claw_free = 0
    scf_rows = []
    collisions = []
    for line in census_payload.splitlines():
        graph6 = line.decode("ascii")
        graph = nx.from_graph6_bytes(line)
        if has_claw(graph):
            continue
        claw_free += 1
        cliques = simplicial_cliques(graph)
        if not cliques:
            continue
        line_graph = is_line_graph(graph)
        row = {
            "graph6": graph6,
            "edges": graph.number_of_edges(),
            "line_graph": line_graph,
            "simplicial_clique_sizes": sorted({len(clique) for clique in cliques}),
        }
        scf_rows.append(row)
        if graph6 in imperfect:
            collisions.append(graph6)

    result = {
        "experiment": "exhaustive_connected_order9_SCF_census",
        "source": CENSUS_URL,
        "source_sha256": CENSUS_SHA256,
        "connected_graphs": len(census_payload.splitlines()),
        "claw_free_graphs": claw_free,
        "SCF_graphs": len(scf_rows),
        "SCF_non_line_graphs": sum(not row["line_graph"] for row in scf_rows),
        "published_imperfect_graphs": len(imperfect),
        "SCF_imperfect_collisions": collisions,
        "status": "collision" if collisions else "no_published_imperfect_collision",
        "SCF_records": scf_rows,
    }
    if result["connected_graphs"] != 261080 or claw_free != 4494:
        raise AssertionError("census count does not match published controls")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "SCF_records"}, indent=2))


if __name__ == "__main__":
    main()
