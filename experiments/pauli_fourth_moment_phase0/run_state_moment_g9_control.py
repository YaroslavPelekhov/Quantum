"""Validate the Python state-moment hierarchy on the published G9 instance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from run_published_g9_control import pauli_word
from run_scf_theta_guided_attack import graph_from_operators
from state_moment_sdp import beta_state_moment_upper


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    words = ["XIII", "IXII", "IIXI", "ZIII", "IZII", "ZZZI", "YZYX", "YYXX", "YXZZ"]
    operators = np.stack([pauli_word(word) for word in words])
    graph = graph_from_operators(operators)
    weights = np.asarray([1, 1, 1, 1, 1, 1, 1, 2, 2], dtype=float)
    first, first_meta = beta_state_moment_upper(graph, weights, order=1)
    second, second_meta = beta_state_moment_upper(graph, weights, order=2)
    result = {
        "experiment": "published_G9_state_moment_SDP_control",
        "published_first_level": 3.236068,
        "computed_first_level": first,
        "published_second_level": 3.044815,
        "computed_second_level": second,
        "first_level": first_meta,
        "second_level": second_meta,
        "status": "reproduced"
        if abs(first - 3.236068) < 2e-5 and abs(second - 3.044815) < 2e-5
        else "failed",
    }
    if result["status"] != "reproduced":
        raise AssertionError(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
