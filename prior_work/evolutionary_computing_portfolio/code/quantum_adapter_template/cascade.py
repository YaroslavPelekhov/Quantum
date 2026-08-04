from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from .models import EvaluationResult, QuantumCandidate, TypedResidual


@dataclass
class QuantumCascadeContext:
    accepted_components: list[str] = field(default_factory=list)
    rejected_templates: list[dict[str, object]] = field(default_factory=list)
    evidence_log: list[dict[str, object]] = field(default_factory=list)
    residuals: list[TypedResidual] = field(default_factory=list)
    best_candidate: QuantumCandidate | None = None
    best_fitness: float = float("-inf")

    def update(self, result: EvaluationResult, candidate: QuantumCandidate, stage: str) -> None:
        self.evidence_log.append(
            {
                "stage": stage,
                "candidate_id": candidate.candidate_id,
                "fitness": result.fitness,
                "passed": result.proof.passed,
                "violations": list(result.proof.violations),
            }
        )
        self.residuals.extend(result.proof.residuals)
        if result.fitness > self.best_fitness:
            self.best_fitness = result.fitness
            self.best_candidate = candidate
        if not result.proof.passed:
            self.rejected_templates.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "stage": stage,
                    "violations": list(result.proof.violations),
                }
            )


@dataclass(frozen=True)
class CascadeStage:
    name: str
    evaluator: Callable[[QuantumCandidate], EvaluationResult]
    admission_threshold: float


def evaluate_in_cascade(
    candidate: QuantumCandidate,
    stages: Iterable[CascadeStage],
    context: QuantumCascadeContext,
) -> EvaluationResult:
    """CIPHER-style cheap-to-expensive evaluation with a shared context.

    A candidate reaches the next fidelity only after passing the current stage
    and meeting its admission threshold. QPU should be the final stage.
    """
    last: EvaluationResult | None = None
    for stage in stages:
        last = stage.evaluator(candidate)
        context.update(last, candidate, stage.name)
        if not last.proof.passed or last.fitness < stage.admission_threshold:
            return last
    if last is None:
        raise ValueError("At least one cascade stage is required")
    return last
