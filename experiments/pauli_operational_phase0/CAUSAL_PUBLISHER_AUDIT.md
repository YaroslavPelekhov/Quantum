# Publisher check and diagonal support dynamics

2026-09-09. Status: verified obstruction for the written map, NOT confirmed
A-star novelty or an audit of the authors' implementation/data.

## Source verification

Downloaded the [publisher PDF](https://quantum-journal.org/papers/q-2025-04-08-1695/pdf/)
and visually inspected complete printed pages 26 and 27 after Poppler rendering.
SHA256: `581a8cf44f2efab4d58322e40fd31ba9f1904df2a0007ebfdc10e882159887b5`.
Equations 46/50 use the Moore-Penrose inverse square root and the sandwich
order transcribed in our checker. Page 27 contains the finite d^(2k)-r
iteration assertion. Thus these are not HTML conversion artifacts.
Our trace-one causality convention retains I_B/d; the missing global
normalization in equation 51 is not the basis of the counterexample.

Algorithm 2 has a maximum-iteration exit and a return statement, but no
explicit failure status after that exit. Its printed index conventions
are not substituted for the unambiguous one-step equation 50. No authors'
implementation has been retrieved. Full-title searches with code/GitHub
and a GitHub-text search of the publisher PDF found no direct repository;
this limited search is NOT evidence that code is unavailable.

## Exact diagonal dynamics (our derivation)

Let rho be diagonal, with probabilities p(a,b,c), and define
M(b,c)=sum_a p(a,b,c), R(c)=sum_b M(b,c). Let n(c) be the number of b
with M(b,c)>0. Empty columns have R(c)=n(c)=0 and are omitted below.
For the normalized equation-50 map, direct multiplication gives

    p'(a,b,c) = p(a,b,c) R(c) / (M(b,c) Z),
    Z = sum_c n(c) R(c).

Zero entries stay zero; positive entries remain positive at every finite
iteration. Hence the counts n(c) are invariant, and induction yields

    R_l(c) = n(c)^l R_0(c) / sum_h n(h)^l R_0(h).

After the first step, M_l(b,c)=R_l(c)/n(c) on the occupied b entries.
The conditional distribution of a given (b,c) remains its initial value.
These identities completely solve the diagonal iteration for any finite
dimensions, not just qubits. They imply:

* A diagonal input becomes causal at a finite positive iteration iff
  every occupied c column has all d input values present. It then takes
  one step. Otherwise at least one positive column stays noncausal at
  every finite step.
* If all occupied columns have the same count s<d, the first iterate is
  a noncausal fixed point. Its squared marginal defect is
  sum_c R(c)^2 (1/s - 1/d).
* If counts differ, the limit keeps only columns with maximal count.
  The limit is causal iff that maximum equals d. Thus asymptotic repair
  can discard positive columns and reduce rank, although finite iterates
  preserve the diagonal rank. This is distinct from finite convergence.

In particular rho=(|000><000|+|111><111|)/2 is a fully separable rank-two
noncausal fixed point, with squared defect 1/4. Entanglement is not needed
for this failure. Rank two also appears in the paper's sampling examples,
but the diagonal family is measure zero in a continuous Ginibre ensemble:
no failure rate for those experiments follows from this fact.

## Verification and limits

`check_diagonal_causal_filter.py` independently computes rational squared
filter multipliers (no eigensolver), checks the rank-two example, and
checks the closed form and finite-causality classification for all 255
nonempty three-qubit diagonal supports, using weights i+1 on supported
entries and six iterates each: 1530 exact comparisons passed. These are
post-hoc structural tests, not 255 random trials or a general proof;
the algebra above is the proof. The two previous exact pure-state checks
also passed again.

## Prior-art boundary

[QETLAB's own OperatorSinkhorn documentation](https://qetlab.com/OperatorSinkhorn)
already warns of failure on low-rank inputs. This is direct documentation
of an existing implementation, not a theorem identifying our map with it.
[Soma and Uschmajew, 2026](https://link.springer.com/article/10.1007/s10107-026-02361-1),
Section 2, Assumption 2.1, requires invertible left/right Gram matrices for
their operator-scaling problem. Their target is fixed identity marginals;
ours contains the changing R(c), so their convergence theorem cannot be
imported without a reduction. The older Leinaas/Myrheim/Ovrum paper
[quant-ph/0605079](https://arxiv.org/abs/quant-ph/0605079) was located but only
its abstract inspected; no theorem-level coverage claim is made for it.

Consequently neither generic low-rank nonconvergence nor this elementary
support-count recurrence is claimed as new. The useful next research gate
is a precise account of noncommuting support dynamics and the induced
sampling measure, compared with established operator scaling and causal
Stinespring constructions. A correction alone is not the requested major
contribution. No large campaign, QPU job, or author contact was initiated.
