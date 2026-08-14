"""Equivalence tests for the memory-bounded exact metric accumulator."""

from __future__ import annotations

import unittest
import json

import numpy as np

import run_exact_extension as extension


class CompiledDecoderTests(unittest.TestCase):
    def assert_equivalent(self, name: str, cap: int, ordering: str, indices) -> None:
        case = extension.resource.prepare_case(name, cap, ordering)
        indices = np.asarray(list(indices), dtype=np.uint64)
        compiled = extension.compile_decoder(case)
        selected, feasible = extension.compiled_outcomes(compiled, indices)
        for position, index_value in enumerate(indices):
            index = int(index_value)
            qbits = "".join(str((index >> qubit) & 1) for qubit in range(case.qubits))
            canonical = extension.resource.canonical_bitstring(case, qbits)
            decoded = case.decoder.decode(canonical)
            self.assertEqual(int(selected[position]), decoded.raw_selected)
            self.assertEqual(bool(feasible[position]), decoded.raw_feasible)

    def test_exhaustive_small_cases(self) -> None:
        for name, cap in (("karate", 4), ("chesapeake", 12), ("football", 10)):
            for ordering in extension.ORDERINGS:
                with self.subTest(name=name, ordering=ordering):
                    case = extension.resource.prepare_case(name, cap, ordering)
                    self.assert_equivalent(name, cap, ordering, range(1 << case.qubits))

    def test_fixed_samples_large_cases(self) -> None:
        rng = np.random.default_rng(20260809)
        for name, cap, sample_count in (
            ("ibm32", 8, 20_000),
            ("aves-sparrow-social", 20, 20_000),
        ):
            for ordering in extension.ORDERINGS:
                with self.subTest(name=name, ordering=ordering):
                    case = extension.resource.prepare_case(name, cap, ordering)
                    indices = rng.integers(
                        0, 1 << case.qubits, size=sample_count, dtype=np.uint64
                    )
                    self.assert_equivalent(name, cap, ordering, indices)

    def test_streaming_metrics_match_frozen_exact_reference(self) -> None:
        reference_path = (
            extension.HERE / "results" / "external_validity" / "exact_statevector.json"
        )
        payload = json.loads(reference_path.read_text(encoding="utf-8"))
        reference = next(
            row
            for row in payload["rows"]
            if row["case"] == "ibm32"
            and row["method"] == "published_lr"
            and row["ordering"] == "sorted"
        )
        case = extension.resource.prepare_case("ibm32", 8, "sorted")
        original_chunk_size = extension.CHUNK_SIZE
        try:
            extension.CHUNK_SIZE = 1 << 10
            actual = extension.streaming_exact_evaluate(
                case,
                np.asarray(extension.METHODS["published_lr"]),
                extension.DEPTH,
            )
        finally:
            extension.CHUNK_SIZE = original_chunk_size
        for metric, expected in reference["metrics"].items():
            if isinstance(expected, (int, float)):
                self.assertAlmostEqual(actual["metrics"][metric], expected, places=12)
            else:
                self.assertEqual(actual["metrics"][metric], expected)


if __name__ == "__main__":
    unittest.main()
