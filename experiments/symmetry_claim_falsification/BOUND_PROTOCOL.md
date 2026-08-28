# Frozen twin-quotient structural-bound audit

Frozen 2026-08-28 after the symmetry-only controls killed the ansatz-specific
interpretation and before evaluating this bound.

For every graph twin class `C_g` and a cut `L|R`, map a basis string to the
count vectors

`pi_L(x) = (|x intersect C_g intersect L|)_g`,

`pi_R(x) = (|x intersect C_g intersect R|)_g`.

Collapse the MIS event to the unique quotient incidence relation

`E_bar = {(pi_L(x), pi_R(x)): x in E}`.

Let `s_L_bar` and `s_R_bar` be its active left and right counts, let
`mu_2_bar` be maximum matching after duplicating each right quotient vertex,
and let `d_L = product_g (|C_g intersect L| + 1)`.  The proposed bound is

`B_twin = min(2 s_L_bar, 4 s_R_bar, 2 mu_2_bar, d_L)`.

The audit evaluates all nontrivial cuts, not only the previously selected
deficits.  The ansatz/event-rank component is considered completely explained
by twin symmetry if all five generic twin-Haar seeds attain `B_twin` on every
cut where the bound is below the dense left dimension, and archived QAOA never
exceeds it.  Any violation rejects the formula.  A QAOA deficit below this new
bound would preserve a narrower ansatz-dependent residual.

The bound implementation must operate only on graph groups and the event set;
it may not inspect amplitudes or archived numerical ranks.
