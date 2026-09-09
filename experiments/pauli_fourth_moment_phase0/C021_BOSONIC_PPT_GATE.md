# C021: identical pure-copy support, beyond standalone PPT

2026-09-09. Frozen before the new run. C020 exactly excludes standalone
PPT as a proof of C014. It does not exclude the stronger condition here.

For nonnegative weights F(rho)=sum w_i< P_i >^2 is convex, hence its maximum
is attained on a pure state. The vector psi⊗psi lies in the symmetric
subspace. Identical Pauli twirling preserves this support. In our Bell
coordinates the swap eigenvalue is tau(v)=(-1)^popcount(x&z). Thus one
can impose lambda_v=0 whenever tau(v)=-1 while preserving a valid upper
relaxation of the pure-state maximum. Mere commutation with swap is not
enough; we require support in its +1 eigenspace. PPT plus this condition
is not asserted to imply separability. Symmetric-support/PPT methods are
known, not a newly invented quantum primitive (see QETLAB SymmetricExtension).

First compute exact antisymmetric mass of C020's certificate, without
changing it. Then run fixed PDHG tau=sigma=.9 on symmetric-support simplex,
with current/average primal checks every 100 iterations. Repair against
the normalized symmetric projector, whose PT is strictly positive. Start
from that projector and zero dual. G8 control then C014; each has 20000
iterations / 60-second cap, one thread, no restarts. Stop a primal search
if repaired value exceeds the corresponding stable bound by .001.
Require the G8 check not to imply an upper bound below its physical >3.0448.

Also log dual candidate upper value max_even(c-A*y) for y<=0, and preserve
the best dual vector. Floating-point upper values are not rigorous proofs.
Any result six needs exact dual inequalities in all coordinates. A primal
above six needs exact positivity, PPT and ZERO antisymmetric mass, not the
previous uniform repair that fills forbidden coordinates. Any near-six
numerical result remains provisional. No graph-general representation or
all-weight claim is inferred from this fixed-label calculation.

## Result: rigorous near-six upper bound, not equality

C020's exact antisymmetric mass is 169343197181/500000010289 (>0), so
that witness is excluded by the new condition. It remains a valid witness
against standalone PPT; there is no contradiction between the two gates.

G8 passed the positive-control check at iteration 100: repaired value
3.33332617 and numerical dual 3.33333620, both above its known physical
violation. C014 reached the fixed 20000-iteration cap in 21.938 seconds.
Best repaired primal was 5.99999999942047; best numerical dual was
6.000000000000007. These floats alone do not prove equality.

Rounded the nonnegative dual u=-y to denominator 10^12 without assuming
that rounding preserved an objective of six. For exact integer T=D*A,
the certificate computes the MAXIMUM of

    c_v + (T*u)_v / (D*10^12), for tau(v)=+1,

and obtains exactly

    153600000000033/25600000000000
      = 6 + 33/25600000000000.

Proof of upper bound: for nonnegative lambda supported on tau=+1 with
sum(lambda)=1 and A*lambda>=0, and u>=0,
c.lambda <= (c+A*u).lambda <= max_even(c+A*u). The transform is real
symmetric. Every pure tensor-square state is included after twirling;
convexity reduces the maximum over input density matrices to pure states.
Thus this is an exact rational uncertainty upper bound for the archived
C014 representation, not merely an eigensolver tolerance.

c021_exact_dual.py regenerates c from local Bell eigenvalue tables and
checks the source hash, all 16384 nonnegative dual coordinates, and all
8256 symmetric-support inequalities. Integer local transforms and integer
Walsh convolution agree in every coordinate. Verification runs with
python -S. Five tests pass, including rejection of a false claim of exactly
six, negative dual entries, missing support condition and changed source.

The positive gap is about 1.2891e-12, not zero. No exact C014 facet theorem,
graph-universal representation result, or A-star novelty is declared.
Post-hoc diagnostics of the numerical solution identify 3808 near-tight
even coordinates / 1046 affine orbits and 3283 positive dual linear orbits.
Those counts suggest a smaller active-constraint certificate recovery
problem, but are not themselves exact active-set certifications.
