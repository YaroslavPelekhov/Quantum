# Causal asymmetric decision-certified bond allocation

## Setting

For trajectory `s` and checkpoint `t`, let `z_(s,t)` be the primary compressed
backward vector and `r_(s,t)=v_(s,t)-z_(s,t)` its exact residual. A scheduled
residual witness uses an arbitrary bond `chi_(s,t)` and recurrence

`rhat_(s,t) = TT_chi(s,t)(U_t^dagger rhat_(s,t+1) + c_(s,t))`,

`xi_(s,t) = xi_(s,t+1) + delta_(s,t) + nu`,

where `delta` is a certified local TT-SVD error and `nu` is the declared
floating-point allowance.

## Lemma 1: arbitrary-schedule residual soundness

For every trajectory, checkpoint, and deterministic or data-dependent bond
schedule that does not use the unknown exact residual,

`||r_(s,t)-rhat_(s,t)||_2 <= xi_(s,t)`.

Proof is backward induction. It is true at the terminal checkpoint. Assuming it
at `t+1`, unitarity preserves the inherited error. TT-SVD adds at most `delta`,
and the numerical allowance adds `nu`. The triangle inequality gives the stated
recurrence. No step requires a constant bond.

## Lemma 2: irreversible certified tail

`xi_(s,t) >= xi_(s,t+1)` for every backward step. Raising the bond at a later
checkpoint may reduce subsequent local `delta` values but cannot reduce any
tail already accumulated at larger checkpoint positions.

This follows immediately because every increment is nonnegative. It explains
why a schedule designed by independently mixing fixed-bond checkpoint rows need
not attain its additive proxy.

## Theorem: trajectory-asymmetric decision certificate

Let each trajectory use its own arbitrary primary and residual bond schedules.
Define

`eta_(s,t) = sum_k min(1, ||rhat_(s,k,t)||_2 + xi_(s,k,t))`

and

`E_s = sum_t (|Tr(Otilde_(s,t) Delta rho_(s,t))|
                   + R_(s,t) eta_(s,t))`,

where `R_(s,t)` soundly bounds `||Delta rho_(s,t)||_1`. Then

`|q_s-p_s| <= E_s`.

For two trajectories A and B, if

`|q_A-q_B| > E_A+E_B`,

the approximate and exact rankings agree.

Proof: Lemma 1 gives the per-vector residual enclosure and therefore the
operator-norm enclosure `eta`. Holder duality bounds each telescope term.
Summation gives the individual intervals. The ranking result follows from the
triangle inequality, without requiring equal bonds or correlated errors.

## Optimization target

The resulting resource problem is

`min sum_(s,t) C_s,t(chi_s,t)` subject to `E_A+E_B < |q_A-q_B|`.

Unlike fixed-bond MPS or a per-state fidelity controller, the allocation unit is
the tuple `(trajectory, checkpoint, witness bond)`. Because of Lemma 2, a sound
online controller must carry the residual witness and scalar tail as causal
state; a checkpoint-wise static knapsack using fixed-bond rows is only a design
heuristic, not a certificate. The executed recurrence always remains the source
of the final guarantee.
