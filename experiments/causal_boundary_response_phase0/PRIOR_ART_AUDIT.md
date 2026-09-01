# Prior-art boundary for causal boundary-response kernelization

The words “memory kernel”, “self-energy”, “response rank”, and “surrogate
mode” are not themselves novel.  The candidate is viable only if it yields a
sublinear *physical Rydberg-atom* replacement with a host-independent
finite-time guarantee and a separation from spatial truncation.

## Direct boundaries

- Feshbach/Nakajima-Zwanzig projection already produces retarded self-energies
  after eliminating degrees of freedom.
- Kempton and Tolbert, *Isospectral reductions and quantum walks on graphs*,
  derive energy-dependent Schur reductions for restricted quantum-walk
  dynamics: <https://arxiv.org/abs/2212.00172>.
- Thoenniss, Vilkoviskiy, and Abanin compress bath memory kernels into
  pseudomodes: <https://arxiv.org/abs/2409.08816>.
- Aharonov and Zhou give general Hamiltonian-simulation and gap-simulation
  limitations: <https://arxiv.org/abs/1804.11084>.
- Generic controlled-response Hankel realization is classical bilinear-system
  theory, not a new simulator: Isidori (1973), Arbib and Manes (1981), and the
  quantum-system identification work of Albertini--D'Alessandro and
  Zhang--Sarovar.
- Exact observable-specific quantum model reduction now includes linear,
  Lindblad, CPTP, and conditional-output constructions; a bare low-rank
  response compiler is therefore outside the novelty boundary.

## Rydberg/MIS boundaries

- Analog counterdiabatic control has already been demonstrated on Aquila:
  <https://arxiv.org/abs/2405.14829>.
- Quantum-aware Rydberg embeddings already address embedding-induced small
  gaps: <https://arxiv.org/abs/2411.04645>.
- qReduMIS already combines classical MIS reductions and Rydberg sampling, but
  does not preserve coherent dynamics through a reduction:
  <https://arxiv.org/abs/2503.12551>.
- Sweep-quench-sweep and Landau-Zener-Stueckelberg schedules already exploit
  diabatic phase interference; a phase kick is not the contribution:
  <https://arxiv.org/abs/2405.21019>.

## Hardware constraint

The intended object must compile to Aquila's fixed geometry, global
`Omega(t)`, global phase, global detuning, and (where enabled) a time-dependent
amplitude multiplying one fixed local-detuning spatial pattern.  Arbitrary
site-dependent transverse drives, a changing spatial mask, or mid-shot
feedback are out of scope.

Official capability references:

- <https://docs.aws.amazon.com/braket/latest/developerguide/braket-quera-submitting-analog-program-aquila.html>
- <https://docs.aws.amazon.com/braket/latest/developerguide/braket-access-local-detuning.html>

