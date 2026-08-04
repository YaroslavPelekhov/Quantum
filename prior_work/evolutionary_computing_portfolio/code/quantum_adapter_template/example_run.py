from __future__ import annotations

from dataclasses import asdict
import json

from .evaluator import evaluate_candidate
from .models import (
    BackendProfile,
    QuantumCandidate,
    RawBackendResult,
    ResourceBudget,
)
from .promotion_gate import held_out_promotion_gate


class DummyBackend:
    """Replace this with a Metriq-Gym, Qiskit Aer, CUDA-Q, or QPU adapter."""

    profile = BackendProfile(
        name="dummy_noisy_simulator",
        num_qubits=24,
        coupling_signature="line-24",
        noise_signature="synthetic-v1",
        is_hardware=False,
    )

    def run(self, candidate: QuantumCandidate, instance_id: str) -> RawBackendResult:
        # Deterministic values keep the example reproducible. A real adapter
        # compiles candidate.source_code, executes it in a sandbox, and verifies
        # the returned assignment using the QOBLIB instance verifier.
        policy_bonus = 0.04 if "warm_start" in candidate.source_code else 0.0
        return RawBackendResult(
            objective_value=84.0,
            best_known_value=100.0,
            approximation_ratio=0.82 + policy_bonus,
            feasibility_rate=0.97,
            probability_best_known=0.08,
            two_qubit_depth=180,
            shots=1024,
            runtime_s=2.8,
            valid_circuit=True,
            classical_baseline_ratio=0.80,
        )


def main() -> None:
    candidate = QuantumCandidate(
        candidate_id="candidate-001",
        policy_name="warm-start-xy",
        source_code="def build_solver(instance, backend): return warm_start(instance)",
    )
    result = evaluate_candidate(
        candidate=candidate,
        instance_id="qoblib-demo-01",
        backend=DummyBackend(),
        budget=ResourceBudget(
            max_qubits=24,
            max_two_qubit_depth=240,
            max_shots=2048,
            max_runtime_s=5.0,
        ),
        robustness_score=0.78,
    )
    print(json.dumps(asdict(result.proof), indent=2, default=str))
    print(f"fitness={result.fitness:.4f}")

    decision = held_out_promotion_gate(
        baseline_scores={"i1-b1": 0.70, "i2-b1": 0.72, "i3-b2": 0.68, "i4-b2": 0.74},
        operator_scores={"i1-b1": 0.75, "i2-b1": 0.76, "i3-b2": 0.72, "i4-b2": 0.77},
        complexity_cost=1.0,
        backend_by_case={"i1-b1": "b1", "i2-b1": "b1", "i3-b2": "b2", "i4-b2": "b2"},
    )
    print(json.dumps(asdict(decision), indent=2))


if __name__ == "__main__":
    main()
