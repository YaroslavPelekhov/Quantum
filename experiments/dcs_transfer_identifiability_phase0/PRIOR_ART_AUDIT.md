# Prior-art boundary

Audit date: 2026-09-03.  This document records the nearest known collisions and
the claim boundary before confirmatory experiments.

## Source under audit

- Martiel et al., *Sampling hard circuits with verifiably high fidelity*,
  arXiv:2607.25941v2: https://arxiv.org/abs/2607.25941

Its exact algebraic fidelity relation is retained after adding the assumptions
of ideal inserted phases and a common stochastic Pauli fault-path distribution.
Our N1 claim concerns the subsequent asymptotic rarity argument, whose proof
uses probability regularity and mixing conditions absent from the theorem
statement.  Our N2 claim concerns what is identifiable from measured reference
fidelity and syndrome data alone.  We do not claim that the reported hardware
state has low fidelity.

## Nearest collisions

1. Merkel et al., *When Clifford benchmarks are sufficient; estimating
   application performance with scalable proxy circuits*, arXiv:2503.05943:
   https://arxiv.org/abs/2503.05943

   This is the strongest collision for a positive companion result.  It uses
   random Cliffordization and proves approximate equality of process metrics to
   lowest order under layer-level Pauli-twirling assumptions.  A surviving claim
   here must instead be a nonperturbative post-selected state-fidelity bound for
   arbitrary correlated stochastic fault paths, or a new impossibility theorem.

2. Xiao et al., *In-situ benchmarking of fault-tolerant quantum circuits. I.
   Clifford circuits*, arXiv:2601.21472:
   https://arxiv.org/abs/2601.21472

   It gives necessary and sufficient learnability conditions for physical and
   logical Pauli noise from syndrome data in Clifford circuits.  It explicitly
   announces a Part II on classically hard circuits.  Generic syndrome
   identifiability, response-matrix rank, or an LP dual witness is therefore not
   sufficient novelty.

3. Girling, Criger, and Cirstoiu, *Characterization of syndrome-dependent
   logical noise in detector regions*, arXiv:2508.08188:
   https://arxiv.org/abs/2508.08188

   This directly estimates syndrome-conditioned logical Pauli channels and has
   trapped-ion validation.  A repair based merely on learning the logical
   channel is occupied.

4. Wagner et al., *Optimal noise estimation from syndrome statistics of quantum
   codes*, Phys. Rev. Research 3, 013292 (2021):
   https://doi.org/10.1103/PhysRevResearch.3.013292

   This establishes identifiability conditions for error rates from syndrome
   data.  Our result must concern cross-circuit non-Clifford fidelity transfer,
   not error-rate estimation in a fixed code.

5. Harper and Flammia, *Estimating the fidelity of T gates using standard
   interleaved randomized benchmarking*, arXiv:1608.02943:
   https://arxiv.org/abs/1608.02943

   This estimates average T-gate fidelity under randomized-benchmarking
   assumptions.  It does not certify the post-selected state fidelity of a
   classically hard circuit under a correlated fault-path distribution.

## Public-data audit

The current Zenodo version is DOI 10.5281/zenodo.22233383, reached from the
version chain of DOI 10.5281/zenodo.21633064.  It contains three 64-qubit payload
QASM files and figure data.  It does not contain the 12-ancilla check circuits,
check back-cumulants, the harmless-fault classifier, the Monte Carlo code, or
the fault-model weights needed to independently reproduce the reported 0.010
conversion penalty.  Consequently, the public archive can validate reported
aggregates and payload structure but cannot serve as an independent audit of
that penalty.

## Novelty decision rule

The work is not positioned as new if it ends with only:

- a missing-assumption correction;
- the two-qubit non-identifiability example;
- a generic moment LP;
- empirical agreement between T and S circuits;
- ordinary random Cliffordization;
- a new name for Pauli-channel learning.

It survives only through one of the two outcomes in `PREREGISTRATION.md`:
a nonperturbative companion certificate with a universal constant, or a
quantum-specific asymptotic barrier with a matching upper bound.

