# C017: bounded two-copy PPT upper-bound route

2026-09-09. Frozen before solving. Target is unchanged C014. Do not add
random-state optimization or reinterpret a relaxed state as a physical
counterexample. Previous turn rejected known hidden-memory novelty and
revalidated the open target.

For fixed Hermitian Pauli P_i and nonnegative w_i let Q=sum w_i P_i⊗P_i.
Then max_rho sum w_i< P_i >_rho^2 equals max over bipartite separable
states Tr(Q sigma): product states obey weighted Cauchy–Schwarz and equal
copies attain the maximum. Relax separability to positivity under partial
transpose (PPT). This is a known relaxation, NOT a new primitive.

Twirling with identical Pauli conjugations on both copies leaves Q fixed,
preserves separability/PPT, and produces a Bell-diagonal state. With
v=(x,z), tau(v)=(-1)^popcount(x&z), its objective eigenvalues are
c_v=sum_i w_i tau(p_i)(-1)^symplectic(v,p_i). Partial transpose sends
Bell probabilities lambda to A lambda, where A_vu=tau(v xor u)/D and
D=2^q. It is a tensor product of q four-by-four transforms. Check this
formula against explicit one-qubit Bell projectors before solving.

Use nonnegative lambda and A lambda with sum(lambda)=1. Avoid a dense
16384-square matrix: introduce free intermediate vectors and apply each
four-by-four transform using sparse linear equalities. No automorphism
averaging or central-sector assertion is needed to build this fixed-
representation relaxation. A final graph-universal proof must separately
justify representation/central-sector coverage.

Cases: published G8 positive-violation control (must not yield bound below
the stored physical value ~3.0448), then C014 seven-qubit target. SciPy
HiGHS dual simplex, one thread, 60-second solver cap per case. Do not
rerun with a changed solver budget after seeing the outcome. Report
dimensions, status, residuals and feasible primal value if returned.
Numerical optimum six is NOT accepted as proof: require a separately
verified rigorous dual certificate in a subsequent step. A feasible PPT
value above six only defeats this proof relaxation, not the inequality.
If timeout/no incumbent, record it as inconclusive without a fake bound.

## Outcome

The explicit one-qubit partial-transpose check passed. G8 solved to a
numerical PPT optimum 3.3333333333333353, consistent with its known
physical value >3.0448. This validates a necessary positive-control check,
not the exact optimum or a complete implementation audit.

C014 produced 131072 variables, 114689 equalities and 589824 nonzeros
instead of a dense 16384-square transform. HiGHS reached its 60-second
limit without a returned primal incumbent (status 1). No C014 bound,
certificate or physical conclusion is available from this run. Runtime
including construction was 60.219 seconds. The budget was not extended.

As a post-hoc exact check of the G8 primal only, rounded its probabilities
to a common denominator and added a uniform rational component sufficient
to make both probabilities and partial-transpose probabilities strictly
positive. Integer transforms were checked against the direct character
matrix for q=3. The resulting exact feasible objective is
333333354/100000135 = 3.333329040005796. This is a LOWER bound on the PPT
relaxation optimum, not a quantum upper certificate or physical violation.
It confirms the relaxation does not incorrectly exclude the positive
control. The objective vector is inherited from the solver setup; a
future exact upper certificate must independently regenerate all input
operators and weights and justify graph-universal representation scope.

Files: run_c017_ppt.py, verify_c017_ppt_primal.py, c017_ppt.json/.npz and
c017_ppt_primal_certificate.json under the existing result directory.
Next computational option is a proved symmetry reduction or a sparse
dual ansatz, not claiming success from timeout or blindly raising budget.
PPT may still be too weak even after solving; this gate remains inconclusive
for C014. No new physical experiments or A-star claim.
