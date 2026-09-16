# C039: centralized baselines and mechanism ablations

Date: 2026-09-16.

## Central research claim

The paper is now organized around one mechanism rather than a list of graph
families:

> If `Q` is a real skew-symmetric contraction, then the squared entries
> `x_uv = Q_uv^2` on any root graph satisfy every degree and odd-set inequality,
> hence `x` belongs to the matching polytope.

Nuclear-norm duality converts this geometric statement into the exact weighted
Pauli identity

`beta(L(R),w) = alpha(L(R),w) = nu(R,w)`.

The experiments below do not replace the proof. They test whether the named
ingredients are necessary, whether standard weaker baselines are sufficient in
practice, and whether the sharp theorem is only a worst-case construction.

## Baselines

All baselines optimize the same nonnegative weighted edge vector.

1. **Degree-only fractional matching:** root-star constraints
   `sum_(e incident v) x_e <= 1`.
2. **Clique + odd-cycle relaxation:** degree constraints, every root-triangle
   clique constraint, and every simple odd-root-cycle constraint. In line-graph
   coordinates this is the standard nonnegativity + clique + odd-hole system
   defining the h-perfect relaxation.
3. **Full matching polytope:** degree constraints and every odd-root-vertex-set
   blossom constraint.
4. **Exact matching:** NetworkX maximum-weight matching, used as the discrete
   reference value.

The complete odd-set description and maximum-weight algorithm originate with
[Edmonds](https://doi.org/10.6028/jres.069B.013). The h-perfect baseline uses
the same clique and odd-hole terminology as the current Pauli beta-number
framework of [Xu et al.](https://arxiv.org/abs/2511.13531).

## Protocol

- All 1245 nonempty unlabeled root graphs in the NetworkX atlas, order at most
  seven.
- Five weight vectors per graph: one uniform and four seeded integer vectors
  with entries in `{1,...,9}`.
- Total: 6225 weighted instances.
- Every LP uses the same edge coordinates and nonnegativity convention.
- The full matching LP is compared against the discrete matching value on every
  instance and must agree within `2e-7` relative tolerance.
- Seed: `20260916`.
- A separate matrix experiment uses four Gaussian coefficient vectors per root
  and a matching-supported equality construction.

The atlas is exhaustive only over *unlabeled graph types* through order seven.
The four nonuniform weights are stress cases, not samples from a claimed
application distribution. Therefore percentages below are descriptive of this
benchmark, not population estimates.

## Baseline results

| Baseline | Mean ratio | Median | 95th percentile | Maximum | Exact instances |
|---|---:|---:|---:|---:|---:|
| Degree only | 1.0351 | 1.0000 | 1.1667 | 1.5000 | 66.89% |
| Cliques + odd cycles | 1.0168 | 1.0000 | 1.1667 | 1.2500 | 84.69% |
| All odd sets | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.00% |

Degree-only is strict on 2061 weighted instances from 797 root graphs.
Clique+odd-cycle is still strict on 953 instances from 555 roots. Thus the
full blossom mechanism is not a decorative proof device: the standard local
relaxations fail repeatedly even at seven root vertices.

The maximum degree-only gap is the uniform triangle: fractional value `3/2`
versus matching value `1`. The maximum h-relaxation gap is `5/2` versus `2`
on a five-vertex, nine-edge root (`graph6 Dn{`); the same ratio `5/4` occurs
for `K5`.

### Positive control: bipartite roots

| Root class | Weighted cases | Degree exact | h-relaxation exact | Full exact |
|---|---:|---:|---:|---:|
| Bipartite | 710 | 100.00% | 100.00% | 100.00% |
| Nonbipartite | 5515 | 62.63% | 82.72% | 100.00% |

The bipartite row recovers the classical fact that degree constraints already
describe the matching polytope for bipartite roots. This is a positive control
for orientation, weights, and LP normalization rather than evidence for a new
claim.

## Blossom ablation on controlled families

For uniform weights on odd roots of order `n`:

| Root family | Matching | Degree-only | h-relaxation | Missing full blossom |
|---|---:|---:|---:|---:|
| Odd cycle `C_n` | `(n-1)/2` | `n/2` | `(n-1)/2` | no |
| Odd complete `K_n` | `(n-1)/2` | `n/2` | `n/2` | additive `1/2` |

Odd-cycle constraints repair the obvious fractional cycle, but do not repair
the full-root blossom in `K_n`. This is the controlled distinction that the
atlas aggregate alone cannot show. The tested table records `n=5,7,9,11,13`.

## Skewness ablation

Skewness is essential, not merely convenient. On `K3`, let

`Q = I - (2/3) J`.

This is a symmetric orthogonal Householder matrix, so `||Q||op=1`. Every
off-diagonal square is `4/9`; all three degree sums are `8/9 <= 1`, but the
odd-set sum is `4/3 > 1`. Thus a general contraction can pass every degree
check and still lie outside the matching polytope.

As a matched control, the `3 x 3` skew cross-product matrix for
`(1,1,1)/sqrt(3)` has operator norm one, edge squares `1/3`, and triangle sum
exactly one. The lost rank of an odd skew matrix is precisely what restores
the blossom constraint.

## Sharpness versus typical directions

The theorem ratio is

`(||A||*/2)^2 / (nu(R,w) sum_e A_e^2/w_e)`.

- 4980 random directions: median `0.3992`, 95th percentile `0.7360`.
- After excluding roots with fewer than three edges or matching value below
  two: 4920 directions, median `0.3968`, 95th percentile `0.7129`.
- One matching-supported direction on every root: all 1245 ratios equal one.

Therefore the constant is globally sharp on every graph and weight vector,
but random coefficient directions are usually far from equality. This is the
right interpretation: the theorem gives an exact worst-case support function,
not a claim that generic Hamiltonians saturate it.

## Figures and machine-readable tables

- `paper_c038/figures/c039_baseline_gaps.png`
- `paper_c038/figures/c039_mechanism_ablations.png`
- `results/pauli_fourth_moment_phase0/c039_baseline_summary.csv`
- `results/pauli_fourth_moment_phase0/c039_by_order.csv`
- `results/pauli_fourth_moment_phase0/c039_family_ablations.csv`
- `results/pauli_fourth_moment_phase0/c039_central_ablations.json`

The JSON records every graph6 identifier, weight vector, LP value, ratio,
aggregate, scope flag, and SHA-256 for the five derived table/figure artifacts.
The standard-library verifier recomputes aggregates, checks all 6225 full-LP
equalities, proves the rational Householder counterexample, checks the family
formulas, and verifies every artifact hash. Five corruption-controlled tests
must reject altered full-polytope ratios, counterexample entries, hashes, or
scope flags.

## Realistic conclusion

The new evidence supports a tightly centralized story:

1. Degree constraints explain bipartite roots but fail on one third of the
   weighted atlas cases.
2. Adding all clique and odd-cycle constraints removes many failures but leaves
   953 strict cases and an infinite controlled family.
3. Full odd-set constraints close every tested case, exactly as the theorem
   predicts.
4. Removing skewness gives an exact `K3` counterexample even though degree
   constraints remain valid.
5. Matching-supported directions prove global sharpness, whereas random
   directions demonstrate that saturation is not typical.

This strengthens mechanism and exposition, not literature priority. It does
not establish a statistical model of real quantum Hamiltonians, runtime
advantage, hardware performance, or a theorem beyond line graphs. Related
free-fermion line-graph structure remains due to
[Chapman--Flammia](https://doi.org/10.22331/q-2020-06-04-278), and classical
skew-energy/matching comparisons exist in
[Tian--Wong](https://doi.org/10.1016/j.dam.2017.01.004).

## Reproduction

```text
python experiments/pauli_fourth_moment_phase0/run_c039_central_ablations.py --overwrite
python -S experiments/pauli_fourth_moment_phase0/verify_c039_central_ablations.py
python -m unittest discover -s experiments/pauli_fourth_moment_phase0 -p test_c039_central_ablations.py -v
```
