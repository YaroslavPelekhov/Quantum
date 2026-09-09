# C020: find and exactly certify a PPT primal, not another upper solver

2026-09-09. Previous turn made progress by constructing verified symmetry
actions and recording failure of 20 partial-constraint LPs. Those were not
PPT-feasible. This changes the numerical method, not the target or budget.

Optimize C014's same full Bell-diagonal PPT LP using primal-dual hybrid
gradient and the orthogonal Walsh representation of partial transpose.
Let t=N*lambda, N=16384. Project t onto t>=0, sum(t)=N and use the dual
negative orthant for A*t>=0. Fixed tau=sigma=0.9 and overrelaxation one;
objective is the archived integer Bell eigenvalue vector. Start uniform,
zero dual; no random seeds or restarts. At most 20000 iterations or 60
seconds on one thread. Evaluate current and running-average iterates
every 100 steps; both are declared before execution.

Repair a candidate by adding uniform mass sufficient to offset the most
negative PT coordinate, then renormalize. Stop if the repaired numerical
objective exceeds 6.001; otherwise preserve the best candidate at the cap.
This is a feasibility search, not a convergence-rate/optimality claim.
Any apparent success must be converted to integer probabilities with a
common denominator, re-repaired exactly, and verified in ALL 16384 original
coordinates with a separately implemented integer PT transform. Regenerate
the objective from the original labels/weights. Acceptance requires exact
nonnegative probabilities, exact nonnegative PT probabilities, trace one
and exact objective >6. Only then conclude PPT cannot prove C014.

Even a successful certificate is NOT a product/separable quantum state and
does NOT refute the desired uncertainty inequality. It kills a proof route,
not the research hypothesis. No claim of novel PDHG or Bell twirling.

## Exact outcome: standalone PPT proof route excluded

At the first registered checkpoint (100 iterations), the last iterate's
uniformly repaired value was 6.56518007190949; runtime 0.187 seconds.
No restart or parameter tuning occurred. Rational conversion at denominator
scale 10^12 plus exact uniform repair yielded objective

    3282590033509 / 500000010289 = 6.565179931919728 > 6.

The exact gap is 282589971775/500000010289. All 16384 integer probability
numerators are positive (minimum 929157), and all unnormalized PT numerators
are positive (minimum 234). Total trace is verified exactly. The certificate
is tied to the original C014 source SHA256; its objective is regenerated
from local one-pair Bell eigenvalue tables and archived labels/weights,
not accepted from the optimization output.

c020_exact_certificate.py verifies every coordinate by both the local
integer transform and an independent integer Walsh convolution. Verification
passes with `python -S`, without NumPy/SciPy. Six stdlib tests pass: valid
certificate, wrong source hash, negative probability, wrong trace, Bell
state violating PPT, and falsified objective. The verification algorithms
are internal, not external peer review.

This is a valid bipartite PPT density matrix but is not supplied as a
separable state or a tensor square rho⊗rho. It proves the standalone
PPT relaxation is too weak; it does NOT prove an uncertainty violation,
give the PPT optimum, or preclude stronger combined constraints/symmetric
extensions. Solving the same complete C017 LP more accurately cannot
produce an upper bound six. Do not spend more CPU on that proof route.

The next unresolved object is separability/tensor-square compatibility
(or an operator proof of C014), not positivity/PPT alone. A higher-order
relaxation needs a separate resource budget and G8 positive control.
A-star novelty remains unconfirmed.
