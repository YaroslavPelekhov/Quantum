# C040--C041: scaled baselines, density stress, and persistent blossoms

Date: 2026-09-16.

## Question

C039 exhaustively settled the small graph atlas. The scaled cycle asks a
different question: do the weaker matching relaxations become effectively
adequate on larger sparse instances, or are their small-graph failures stable
under size, weight heterogeneity, density, and weak inter-block coupling?

The experiments remain mechanism tests. They neither replace the all-size
analytic theorem nor define a probability model for quantum applications.

## C040 protocol

- Orders `10,14,18,22,26,30`.
- Six seeded replicates at each order.
- Five graph generators: sparse Erdos--Renyi, cubic random regular,
  Watts--Strogatz, random geometric, and Barabasi--Albert.
- Total: 180 root graphs.
- Four edge-weight regimes per graph: uniform, integer `1..9`, clipped
  lognormal, and clipped Pareto.
- Total: 720 weighted instances.
- Baselines: degree only; all line-graph clique constraints; then every simple
  odd-root-cycle inequality through length 5, 7, and 9.
- Exact maximum-weight matching is the reference value.
- Forty instances at orders 10 and 14 additionally enumerate every odd vertex
  set and solve the full blossom LP.

The cycle enumeration is complete through the stated cutoff; no cycle sampling
is used. Baselines `odd5`, `odd7`, and `odd9` are deliberately truncated and
must not be called the complete h-perfect relaxation on general larger roots.

## C040 results

| Baseline | Mean ratio | 95th pct. | Maximum | Exact fraction |
|---|---:|---:|---:|---:|
| Degree only | 1.007353 | 1.045550 | 1.500000 | 77.22% |
| + all cliques | 1.002541 | 1.013284 | 1.166667 | 91.67% |
| + odd cycles through 5 | 1.002156 | 1.008641 | 1.166667 | 93.47% |
| + odd cycles through 7 | 1.002068 | 1.005697 | 1.166667 | 93.89% |
| + odd cycles through 9 | 1.002041 | 1.005697 | 1.166667 | 93.89% |

All 40 full-blossom LP spot checks equal exact matching. The local hierarchy
does become numerically close on most random sparse cases, but it does not
converge monotonically to exactness as order grows: the odd-through-9 exact
fraction is 98.33% at order 10 and 90.00% at order 30 in this fixed sample.

### Weight ablation

| Weights | Degree exact | Clique exact | Odd-through-9 exact | Odd-through-9 max |
|---|---:|---:|---:|---:|
| Uniform | 83.33% | 86.67% | 87.22% | 1.166667 |
| Integer | 70.56% | 90.56% | 93.33% | 1.016667 |
| Lognormal | 86.67% | 97.22% | 99.44% | 1.001667 |
| Pareto | 68.33% | 92.22% | 95.56% | 1.030305 |

Weight heterogeneity often breaks degeneracies and makes exactness more common,
but this is distribution-dependent. It is not a theorem that heterogeneous
weights are easier.

### Graph-family ablation

The geometric ensemble is the hardest sampled family: odd-through-9 is exact
on 80.56% and reaches ratio 1.166667. Preferential and random-regular roots are
exact on 99.31% under the same baseline. These percentages are descriptive of
the frozen seeds, not confidence estimates for those random-graph models.

### Structured scaling controls

Disjoint unions make the missing constraint persist instead of disappear with
size. The largest tested roots have 36 to 132 vertices.

| Component | First repairing row | Ratio before repair | Persists under scaling |
|---|---|---:|---:|
| `K3` | clique | 1.500000 | yes |
| `C5` | odd cycle 5 | 1.250000 | yes |
| `C7` | odd cycle 7 | 1.166667 | yes |
| `C9` | odd cycle 9 | 1.125000 | yes |
| `C11` | cycle beyond cutoff | 1.100000 | yes |
| `K5` | full blossom | 1.250000 | yes |

The `K5` row is the decisive distinction: all its simple odd cycles already
have length at most five, yet the complete local clique-and-cycle system stays
at 5/2 while matching is 2. Repeating the component preserves ratio 5/4.

### Matrix-bound scaling

For 540 Gaussian coefficient directions on the larger random roots, the median
theorem ratio is 0.3315, the 95th percentile is 0.4982, and the maximum is
0.7418. Matching-supported directions attain one on all 180 roots. Thus the
larger campaign strengthens the previous interpretation: the constant is
globally sharp but generic Gaussian directions move farther from saturation.

Removing skewness also scales. A block diagonal direct sum of the symmetric
three-dimensional Householder counterexample has degree sums 8/9 and
odd-set-to-matching ratio 4/3 at orders `3,6,12,24,48,96`. The failure is not
a small-matrix accident.

## C041 density stress

C041 uses 45 additional Erdos--Renyi roots at orders 20, 30, and 40, expected
degrees 2 through 6, three replicates, and uniform plus integer weights: 90
weighted instances. The cycle system is again complete through length nine.

- Odd-through-9 is strict in 5/90 instances.
- Maximum remaining ratio is `29/28 = 1.035714...`.
- The largest instance contains 384,484 enumerated odd cycles through length
  nine.
- The full run takes 393.7 seconds and peaks around 1.2 GB working memory on
  the local workstation.

The relation with density is nonmonotone in this small seeded sweep. More
cycles can repair fractional solutions, while denser graphs can also contain
larger odd sets not represented by the cutoff. Therefore the data do not
support a simple claim that density monotonically helps or hurts.

## C041 weak-coupling ablation

To test whether the persistent `K5` gap is an artifact of disconnected unions,
even numbers of `K5` blocks are joined in a ring by one designated bridge per
neighboring pair. Internal weights are one and bridge weight is epsilon.
Orders reach 80 vertices.

The local odd-through-9 optimum remains `2.5 b` for `b` blocks, while matching
is `2 b + epsilon b/2`. The observed ratio is exactly

`2.5 / (2 + epsilon/2)`.

| Bridge weight | Ratio |
|---:|---:|
| 0.00 | 1.250000 |
| 0.01 | 1.246883 |
| 0.10 | 1.219512 |
| 0.25 | 1.176471 |
| 0.50 | 1.111111 |
| 1.00 | 1.000000 |

All four sizes (`2,4,8,16` blocks) lie on the same curve. Hence the obstruction
survives connectivity and weak coupling; it disappears only when the bridges
are strong enough to match every formerly exposed block vertex at full weight.
This is a controlled weighted construction, not evidence about a natural
hardware distribution.

## Reproducibility and negative controls

The frozen package contains two JSON records, seven C040 table/figure hashes,
three C041 hashes, standard-library verifiers, and eleven corruption tests.
The verifiers independently recompute every aggregate, enforce nested-baseline
monotonicity, check all 40 full-blossom spot checks, prove the structured
ratios and weak-coupling formula, and reject scope or artifact corruption.

```text
python experiments/pauli_fourth_moment_phase0/run_c040_scaled_ablations.py --overwrite
python -S experiments/pauli_fourth_moment_phase0/verify_c040_scaled_ablations.py
python experiments/pauli_fourth_moment_phase0/run_c041_density_coupling_stress.py --overwrite
python -S experiments/pauli_fourth_moment_phase0/verify_c041_density_coupling_stress.py
python -m unittest discover -s experiments/pauli_fourth_moment_phase0 -p "test_c04*.py" -v
```

## Realistic conclusion

The scaled evidence does not create a new theorem beyond C038. It does resolve
three empirical questions:

1. Local constraints are often nearly exact on seeded larger sparse graphs,
   especially under strongly heterogeneous weights.
2. That typical behavior is not uniform: explicit families retain constant
   gaps at arbitrary size, and weak coupling does not immediately remove them.
3. Enumerating local odd cycles itself becomes expensive (hundreds of thousands
   of rows by 40 vertices), whereas exact weighted matching remains the correct
   complete reference object.

This strengthens the paper's mechanism and practical interpretation. It does
not establish quantum advantage, an application distribution, or external
priority for the all-line-graph theorem.
