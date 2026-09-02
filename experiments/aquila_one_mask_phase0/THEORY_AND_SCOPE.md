# Theory and claim boundary

## Algebraic resolution in the hard-blockade subspace

For independent sets `S` of a graph, define projected flips
`a_i = P sigma_i^+ P`, `X_i = a_i+a_i^dagger`, and
`Y_i = -i(a_i-a_i^dagger)`.  With `N=sum_i n_i` and
`D_h=sum_i h_i n_i`,

`[N,a_i]=a_i` and `[D_h,a_i]=h_i a_i`.

Thus global `Y` follows from global `X` and `N`.  Moreover the superoperator
`V(K)=[N,[D_h,K]]` obeys `V(X_i)=h_i X_i`.  Distinct `h_i` permit a Lagrange/
Vandermonde interpolation of every projected site flip.  This is an algebraic
statement only.  It does not prove full `su(d)`, finite-time reachability under
one-sided controls, good conditioning, or hardware-scale synthesis.

Exceptions matter.  Equal labels can be separated by different graph
neighbourhoods; conversely distinct labels do not generate entanglement in an
empty graph.  A mask-preserving graph automorphism is a rigorous obstruction to
full controllability, but absence of visible automorphisms is not a proof.

## Reflection ceiling

For the symmetric P4 geometry, every global-only generator commutes with the
reflection `Pi`.  Since `Pi|0000>=|0000>` and it exchanges the two selected MIS
states, their terminal probabilities are equal for every global-only schedule.
They sum to at most one, giving the exact per-target ceiling `F<=1/2`.  A
uniform mask is proportional to `N` and obeys the same theorem.

## Phase gauge

In the AWS convention the global drive is proportional to
`exp(i phi) sigma^- + exp(-i phi) sigma^+`.  The rotation
`R=exp(-i phi N)` removes `phi` and changes global detuning to
`Delta_g + dot(phi)`, plus endpoint number rotations.  Phase may still help a
time-optimal bounded-control schedule because the transformed detuning can
violate a hardware bound, but it is not another spatial pattern.

## Bounded local-detuning action

For a one-sign waveform `u`, define `A=int |u(t)| dt`.  If two otherwise
identical frequency classes differ by `delta=|h_i-h_j|`, Duhamel continuity
bounds how differently a common pulse can act on them.  For the two-frequency
unitary task X-versus-I, after removing global phase,

`delta A / 2 >= sqrt(2) - 2 eta`,

where `eta` is operator-norm error at each endpoint.  Therefore labels packed
in `[0,1]` obey the necessary capacity bound

`n <= 1 + A / (2 (sqrt(2)-2 eta))`.

For preparation of orthogonal targets at permutation-equivalent sites with
infidelity `epsilon`, a Fubini-Study version gives

`delta A >= pi/2 - 2 asin(sqrt(epsilon))`.

These bounds require a genuine twin/ensemble comparison; arbitrary geometry
can itself distinguish sites.  They are necessary bounds, not pulse
constructions.

If `|u|<=Lambda`, `|du/dt|<=R`, and both endpoints are zero, the exact maximum
action is

`A_max(T)=R T^2/4` for `T<=2 Lambda/R`, and
`A_max(T)=Lambda T-Lambda^2/R` otherwise.

The numerical report evaluates this formula using the provisional constraint
snapshot and keeps the result explicitly conditional on a live refresh.

## What this Phase 0 can establish

It can establish a reproducible small-system hardware candidate, a strict
symmetry baseline, a gap between Lie rank and bounded-time fidelity, or a clean
negative result.  It cannot establish scalable universal control, quantum
advantage, topological transport, or A-star novelty.

