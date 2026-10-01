# C047: independent-runtime external oracle

Frozen on 1 October 2026 before the executable was run.

## Purpose

Falsify the weighted skew-matrix inequality used by the line-graph Pauli
theorem with an implementation that shares neither Python code nor numerical
linear-algebra dependencies with the research pipeline.

## Independent stack

- C# / .NET 8 standard library only;
- a fresh SplitMix64 generator and Box--Muller Gaussian sampler;
- exact maximum-weight matching by subset dynamic programming, not NetworkX;
- singular values from a handwritten Jacobi eigensolver for `-A^2`, not NumPy,
  SciPy, or a matching-polytope implementation.

## Frozen challenge set

- Structured roots: paths, cycles, stars, complete graphs, and complete
  bipartite graphs through order 9.
- Twelve seeded Erdos--Renyi roots at each order 3 through 9, cycling through
  edge probabilities 0.25, 0.50, and 0.75.
- Eight independent positive weight vectors per root.
- Four Gaussian skew directions per weight vector.
- One matching-supported equality direction per weight vector.

For every random direction the oracle checks

`(||A||_*/2)^2 <= nu(R,w) * sum_e A_e^2 / w_e`.

For every equality direction, `A_e=w_e` on a maximum-weight matching and zero
elsewhere, the ratio must equal one. The frozen rejection threshold is
`1e-8` for inequality violations and `2e-8` for equality residuals.

This is an independent computational falsification and portability test. It
does not replace proof review, certify bibliographic priority, or constitute
formal verification.
