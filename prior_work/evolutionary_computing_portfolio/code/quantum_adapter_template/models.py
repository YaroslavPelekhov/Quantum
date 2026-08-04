from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


class ResidualType(str, Enum):
    INVALID_CIRCUIT = "INVALID_CIRCUIT"
    INFEASIBLE_SAMPLE = "INFEASIBLE_SAMPLE"
    CONSTRAINT_LEAKAGE = "CONSTRAINT_LEAKAGE"
    DEPTH_EXPLOSION = "DEPTH_EXPLOSION"
    CONNECTIVITY_MISMATCH = "CONNECTIVITY_MISMATCH"
    SHOT_INEFFICIENCY = "SHOT_INEFFICIENCY"
    NOISE_COLLAPSE = "NOISE_COLLAPSE"
    INSTANCE_OVERFIT = "INSTANCE_OVERFIT"
    CLASSICAL_DOMINANCE = "CLASSICAL_DOMINANCE"
    DECOMPOSITION_LOSS = "DECOMPOSITION_LOSS"


@dataclass(frozen=True)
class ResourceBudget:
    max_qubits: int
    max_two_qubit_depth: int
    max_shots: int
    max_runtime_s: float


@dataclass(frozen=True)
class QuantumCandidate:
    candidate_id: str
    source_code: str
    policy_name: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BackendProfile:
    name: str
    num_qubits: int
    coupling_signature: str
    noise_signature: str
    is_hardware: bool = False


@dataclass(frozen=True)
class RawBackendResult:
    objective_value: float
    best_known_value: float
    approximation_ratio: float
    feasibility_rate: float
    probability_best_known: float
    two_qubit_depth: int
    shots: int
    runtime_s: float
    valid_circuit: bool = True
    classical_baseline_ratio: float = 1.0
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TypedResidual:
    residual_type: ResidualType
    location: str
    violated_contract: str
    evidence: Mapping[str, Any]
    validator: str


@dataclass(frozen=True)
class VerificationProof:
    candidate_id: str
    backend: str
    instance_id: str
    satisfied: Sequence[str]
    violations: Sequence[str]
    residuals: Sequence[TypedResidual]
    metrics: Mapping[str, float]
    passed: bool


@dataclass(frozen=True)
class EvaluationResult:
    fitness: float
    proof: VerificationProof
    raw: RawBackendResult
