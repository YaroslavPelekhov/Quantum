"""Parse Aer 0.17.2 matrix-product-state debug logs."""

from __future__ import annotations

import re
import math
from dataclasses import dataclass, asdict


DISCARDED_RE = re.compile(
    r"discarded_value\s*=\s*(?P<value>[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"
)
BOND_RE = re.compile(r"BD=\[(?P<values>[0-9 ]*)\]")
INSTRUCTION_RE = re.compile(
    r"I(?P<index>\d+):(?P<gate>.*?) on qubits "
    r"(?P<qubits>\d+(?:,\d+)*)"
)
TOKEN_RE = re.compile(r"I\d+:|internal_swap on qubits")


@dataclass(frozen=True)
class TruncationEvent:
    event_index: int
    discarded_weight: float
    reported_text: str
    certificate_weight_upper_bound: float
    instruction_index: int | None
    gate: str | None
    qubits: tuple[int, ...]
    bond_dimensions: tuple[int, ...]
    segment: str


def printed_double_upper_bound(value: float, significant_digits: int = 6) -> float:
    """Upper endpoint for C++ defaultfloat output at the given precision."""
    if not math.isfinite(value) or value <= 0.0:
        if value == 0.0:
            return 0.0
        raise ValueError(f"Invalid logged discarded weight: {value}")
    exponent = math.floor(math.log10(value))
    decimal_quantum = 10.0 ** (exponent - significant_digits + 1)
    return min(1.0, math.nextafter(value + 0.5 * decimal_quantum, math.inf))


def parse_mps_log(raw_log: str, include_segments: bool = True) -> dict:
    if not isinstance(raw_log, str):
        raise TypeError("Aer MPS log must be a string")
    text = raw_log.strip()
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1]
    token_matches = list(TOKEN_RE.finditer(text))
    segments = [
        text[match.start() : token_matches[index + 1].start() if index + 1 < len(token_matches) else len(text)]
        for index, match in enumerate(token_matches)
    ]
    events: list[TruncationEvent] = []
    all_bonds: list[int] = []
    parsed_segments = []
    contexts = []
    for segment in segments:
        instruction = INSTRUCTION_RE.search(segment)
        bonds_match = BOND_RE.search(segment)
        bonds = tuple(
            int(value) for value in bonds_match.group("values").split() if value
        ) if bonds_match else ()
        all_bonds.extend(bonds)
        if instruction:
            instruction_index = int(instruction.group("index"))
            gate = instruction.group("gate").strip()
            qubits = tuple(int(value) for value in instruction.group("qubits").split(","))
        else:
            instruction_index = None
            gate = "internal_swap" if "internal_swap on qubits" in segment else None
            qubit_match = re.search(r"internal_swap on qubits ([0-9]+),([0-9]+)", segment)
            qubits = tuple(map(int, qubit_match.groups())) if qubit_match else ()
        parsed_segments.append({
            "instruction_index": instruction_index,
            "gate": gate,
            "qubits": list(qubits),
            "bond_dimensions": list(bonds),
            "raw": segment.strip(),
        })
        contexts.append((instruction_index, gate, qubits, bonds, segment.strip()))
    direct_weights = [float(match.group("value")) for match in DISCARDED_RE.finditer(text)]
    # Aer logs a discarded value inside the gate implementation, then writes
    # the I<n>/internal_swap record and post-gate bond dimensions.  Therefore
    # an event belongs to the first operation token following its text offset.
    for discarded_match in DISCARDED_RE.finditer(text):
        context_index = next(
            (index for index, token in enumerate(token_matches) if token.start() > discarded_match.start()),
            None,
        )
        if context_index is None:
            raise ValueError("discarded_value has no following Aer operation record")
        instruction_index, gate, qubits, bonds, segment = contexts[context_index]
        events.append(
            TruncationEvent(
                event_index=len(events),
                discarded_weight=float(discarded_match.group("value")),
                reported_text=discarded_match.group("value"),
                certificate_weight_upper_bound=printed_double_upper_bound(
                    float(discarded_match.group("value"))
                ),
                instruction_index=instruction_index,
                gate=gate,
                qubits=qubits,
                bond_dimensions=bonds,
                segment=segment,
            )
        )
        parsed_segments[context_index].setdefault("discarded_weights", []).append(
            float(discarded_match.group("value"))
        )
    for segment in parsed_segments:
        segment.setdefault("discarded_weights", [])
    event_weights = [event.discarded_weight for event in events]
    if direct_weights != event_weights:
        raise ValueError("Parser lost or reordered discarded_value entries")
    result = {
        "events": [asdict(event) for event in events],
        "discarded_weights": direct_weights,
        "certificate_weight_upper_bounds": [
            event.certificate_weight_upper_bound for event in events
        ],
        "logging_numeric_precision_significant_digits": 6,
        "number_of_truncations": len(direct_weights),
        "sum_discarded_weight": sum(direct_weights),
        "max_discarded_weight": max(direct_weights, default=0.0),
        "max_bond_seen": max(all_bonds, default=1),
    }
    if include_segments:
        result["raw_log"] = raw_log
        result["segments"] = parsed_segments
    return result
