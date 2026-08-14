# Expanded QOBLIB cohort screen report

The preregistered screen completed all 50 QOBLIB MIS instances and 417
case/cap attempts.  No MILP timed out or failed.  Peak process working set was
3.84 GiB and total wall time was 461.5 seconds.

## Result

- 307 attempts reduced to an empty deterministic kernel.
- 84 attempts remained above the frozen 24-qubit limit.
- 26 attempts produced a non-empty kernel of at most 24 qubits and received
  an exact reduced-MIS certificate.
- 18 of those certified kernels could not attain the original QOBLIB BKS
  after no-repair unfolding.
- Only 8/50 instances satisfied the complete primary eligibility rule; all
  eight have an `optimal` QOBLIB status.

| Case | Qubits | Selected cap | Family | Prior cross-backend anchor |
|---|---:|---:|---|:---:|
| aves-sparrow-social | 24 | 20 | animal network | yes |
| chesapeake | 7 | 12 | named network | yes |
| football | 7 | 16 | named network | yes |
| ibm32 | 18 | 8 | hardware graph | yes |
| karate | 3 | 32 | named network | yes |
| es60fst03 | 12 | 4 | es60 | no |
| mammalia-kangaroo-interactions | 15 | 32 | animal network | no |
| es60fst01 | 15 | 4 | es60 | no |

The target of 15 cases was therefore not reached.  Expanding to 15 by relaxing
the qubit limit or accepting BKS-unreachable reductions would change the
estimand and introduce avoidable selection bias.  The three genuinely new
eligible cases were advanced to the Aer pilot; all exclusions remain in
`results/qoblib_cohort_screen/screen.json`.
