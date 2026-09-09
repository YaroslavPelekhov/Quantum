# C018: exact symmetry reduction of the fixed PPT relaxation

2026-09-09, frozen before execution. C017 timed out with no C014 bound.
Use weight-preserving graph automorphisms only if they induce a consistent
symplectic linear map S on all 24 archived Pauli labels. Invalid maps are
rejected, not assumed to be Clifford symmetries.

For binary v=(x,z), q(v)=x.z mod 2. Define delta by
q(Sv+delta)=q(v) for every v. Verify this identity exhaustively on all
16384 labels, as well as symplecticity and preservation of the objective.
Bell probabilities transform affinely, v -> Sv+delta; partial-transpose
probabilities transform linearly, v -> Sv. The identity
A_(Sv,Su+delta)=A_(v,u) follows directly from q(S(v+u)+delta)=q(v+u).
Thus averaging over the generated finite group preserves both positivity
constraints, trace and objective. Orbit reduction preserves the LP optimum.
This is reduction of a known relaxation, not new quantum physics.

Enumerate at most 256 graph automorphisms with a 20-second discovery cap;
an incomplete enumeration still generates a valid subgroup. Report both
affine and linear orbit counts. Build the reduced PPT coefficients with
integer transforms and orbit counts, then divide by D times orbit size
for orbit-mass variables. Construction cap 60 seconds, dense reduced
matrix cap 10 million entries; stop without solving if exceeded.
HiGHS dual simplex, one thread, 60-second solve cap, unchanged target.
Save permutations/maps, orbits and any solution. Verify a returned primal
on all unreduced coordinates. Value six still needs rigorous dual proof;
a feasible PPT value above six is not a physical violation. No budget
extension after seeing results; no graph/all-weight conclusion assumed.

Outcome: all 16 enumerated weight-preserving automorphisms induced valid
symplectic maps; none rejected, enumeration completed. Every objective
and quadratic-phase identity passed on all 16384 labels. Both partitions
have 5184 orbits. The reduced dense matrix would have 26873856 entries,
so the registered 10-million-entry construction cap stopped this run
before matrix construction or solving. No C014 bound was produced.
Partitions and maps are saved in c018_ppt_symmetry.json; the NPZ is empty
because the construction was intentionally not performed. C019 is a
separately registered constraint-generation method, not a raised size cap.
