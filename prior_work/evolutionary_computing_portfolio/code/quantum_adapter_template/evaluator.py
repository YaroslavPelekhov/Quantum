from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import (
    BackendProfile,
    EvaluationResult,
    QuantumCandidate,
    RawBackendResult,
    ResidualType,
    ResourceBudget,
    TypedResidual,
    VerificationProof,
)


class QuantumBackend(Protocol):
    """Adapter implemented by a Qiskit/CUDA-Q/Metriq-Gym runner."""

    profile: BackendProfile

    def run(self, candidate: QuantumCandidate, instance_id: str) -> RawBackendResult:
        ...


@dataclass(frozen=True)
class FitnessWeights:
    quality: float = 1.0
    feasibility: float = 0.35
    probability_best: float = 0.15
    robustness: float = 0.20
    depth_penalty: float = 0.15
    shot_penalty: float = 0.05
    runtime_penalty: float = 0.10


def evaluate_candidate(
    candidate: QuantumCandidate,
    instance_id: str,
    backend: QuantumBackend,
    budget: ResourceBudget,
    weights: FitnessWeights = FitnessWeights(),
    robustness_score: float = 1.0,
) -> EvaluationResult:
    """RAVR-S-style verifier: return a scalar fitness and an auditable proof object.

    The backend performs the domain-specific execution. This function owns the
    benchmark-independent contract checks and typed residual generation.
    """
    raw = backend.run(candidate, instance_id)
    satisfied: list[str] = []
    violations: list[str] = []
    residuals: list[TypedResidual] = []

    def fail(kind: ResidualType, contract: str, evidence: dict[str, object], location: str) -> None:
        violations.append(contract)
        residuals.append(
            TypedResidual(
                residual_type=kind,
                location=location,
                violated_contract=contract,
                evidence=evidence,
                validator="quantum_contract_verifier_v1",
            )
        )

    if raw.valid_circuit:
        satisfied.append("VALID_CIRCUIT")
    else:
        fail(ResidualType.INVALID_CIRCUIT, "VALID_CIRCUIT", {}, "circuit")

    if raw.feasibility_rate >= 0.95:
        satisfied.append("FEASIBILITY_RATE")
    else:
        fail(
            ResidualType.INFEASIBLE_SAMPLE,
            "FEASIBILITY_RATE>=0.95",
            {"observed": raw.feasibility_rate},
            "sampling/postprocess",
        )

    if raw.two_qubit_depth <= budget.max_two_qubit_depth:
        satisfied.append("TWO_QUBIT_DEPTH_BUDGET")
    else:
        fail(
            ResidualType.DEPTH_EXPLOSION,
            f"two_qubit_depth<={budget.max_two_qubit_depth}",
            {"observed": raw.two_qubit_depth},
            "transpilation",
        )

    if raw.shots <= budget.max_shots:
        satisfied.append("SHOT_BUDGET")
    else:
        fail(
            ResidualType.SHOT_INEFFICIENCY,
            f"shots<={budget.max_shots}",
            {"observed": raw.shots},
            "execution",
        )

    if raw.runtime_s <= budget.max_runtime_s:
        satisfied.append("RUNTIME_BUDGET")
    else:
        fail(
            ResidualType.SHOT_INEFFICIENCY,
            f"runtime_s<={budget.max_runtime_s}",
            {"observed": raw.runtime_s},
            "execution",
        )

    if raw.approximation_ratio >= raw.classical_baseline_ratio:
        satisfied.append("NON_DOMINATED_BY_CLASSICAL_BASELINE")
    else:
        fail(
            ResidualType.CLASSICAL_DOMINANCE,
            "approximation_ratio>=classical_baseline_ratio",
            {
                "candidate": raw.approximation_ratio,
                "classical": raw.classical_baseline_ratio,
            },
            "objective",
        )

    # Resource quantities are normalized by the declared budget so the fitness
    # remains comparable across candidate policies in one resource regime.
    depth_fraction = raw.two_qubit_depth / max(1, budget.max_two_qubit_depth)
    shot_fraction = raw.shots / max(1, budget.max_shots)
    runtime_fraction = raw.runtime_s / max(1e-9, budget.max_runtime_s)

    fitness = (
        weights.quality * raw.approximation_ratio
        + weights.feasibility * raw.feasibility_rate
        + weights.probability_best * raw.probability_best_known
        + weights.robustness * robustness_score
        - weights.depth_penalty * depth_fraction
        - weights.shot_penalty * shot_fraction
        - weights.runtime_penalty * runtime_fraction
    )

    hard_violations = {"VALID_CIRCUIT", "FEASIBILITY_RATE>=0.95"}
    passed = not any(v in hard_violations for v in violations)
    proof = VerificationProof(
        candidate_id=candidate.candidate_id,
        backend=backend.profile.name,
        instance_id=instance_id,
        satisfied=tuple(satisfied),
        violations=tuple(violations),
        residuals=tuple(residuals),
        metrics={
            "approximation_ratio": raw.approximation_ratio,
            "feasibility_rate": raw.feasibility_rate,
            "probability_best_known": raw.probability_best_known,
            "two_qubit_depth": float(raw.two_qubit_depth),
            "shots": float(raw.shots),
            "runtime_s": raw.runtime_s,
            "robustness": robustness_score,
        },
        passed=passed,
    )
    return EvaluationResult(fitness=fitness, proof=proof, raw=raw)
