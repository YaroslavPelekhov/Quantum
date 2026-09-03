"""Screen the pinned hbar-imperfect benchmark sets for the SCF property."""

from __future__ import annotations

import ast
import hashlib
import json
import urllib.request
from pathlib import Path

import networkx as nx

from run_scf_hbar_falsification import has_claw, simplicial_cliques


COMMIT = "467eb611c09631fcf310da8dc73c35cb3b8fe098"
BASE = f"https://raw.githubusercontent.com/wangjie212/BetaNumber/{COMMIT}/src/seesaw-shadow-tomography/data"
EXPECTED = {
    "test8.txt": "96d6ad0be933af0c4f763dc8e5a08d825d413b053235a91cf9340d8ca1a3adbd",
    "test9.txt": "1eb261786d59004f6373b54016ca55c88a36b6f2bdb01edbe538d71b2f69ede7",
    "ndelta8_3_hard.txt": "7156fb0a21b35bdfce27be8b2afac7e38f57647c29efb04abaedcb740f210f68",
    "ndelta9_3_hard.txt": "63e221d0cb4367d067295ca0923117e7fa69847050ad285d6715298fbe460861",
}


def fetch(name: str) -> str:
    with urllib.request.urlopen(f"{BASE}/{name}") as response:
        payload = response.read()
    expected = EXPECTED.get(name)
    if expected and hashlib.sha256(payload).hexdigest() != expected:
        raise AssertionError(f"upstream hash mismatch for {name}")
    return payload.decode("utf-8")


def classify(entries) -> dict:
    graphs = [nx.from_graph6_bytes(entry[0].encode()) for entry in entries]
    claw_free = [not has_claw(graph) for graph in graphs]
    simplicial = [bool(simplicial_cliques(graph)) for graph in graphs]
    connected = [nx.is_connected(graph) for graph in graphs]
    scf = [a and b and c for a, b, c in zip(claw_free, simplicial, connected)]
    return {
        "graphs": len(graphs),
        "connected": sum(connected),
        "claw_free": sum(claw_free),
        "has_simplicial_clique": sum(simplicial),
        "SCF": sum(scf),
        "SCF_graph6": [entry[0] for entry, flag in zip(entries, scf) if flag],
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {
        "experiment": "published_hbar_imperfect_benchmark_SCF_screen",
        "upstream_repository": "https://github.com/wangjie212/BetaNumber",
        "upstream_commit": COMMIT,
        "files": {},
    }
    for order in (8, 9):
        test_name = f"test{order}.txt"
        hard_name = f"ndelta{order}_3_hard.txt"
        tests = [
            ast.literal_eval(line)
            for line in fetch(test_name).splitlines()
            if line.strip()
        ]
        hard = ast.literal_eval(fetch(hard_name))
        selected = [tests[row[0] - 1] for row in hard]
        result["files"][test_name] = {
            "sha256": EXPECTED[test_name],
            "all": classify(tests),
            "hard_subset": classify(selected),
        }
    result["status"] = (
        "structural_collision"
        if any(data[subset]["SCF"] for data in result["files"].values() for subset in ("all", "hard_subset"))
        else "no_SCF_graph_in_published_imperfect_sets"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
