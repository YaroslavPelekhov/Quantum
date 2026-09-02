# Exploratory disclosure

This experiment is not presented as a blind discovery run.

Before the validation protocol was frozen, a read-only numerical search found a
two-atom development pulse with a principal-log plaquette phase near `pi/2` and
a forward/reverse counts asymmetry near `0.24`.  The exact development pulse is
recorded in `protocol.json`.  It is used only as a regression and robustness
case.

The following were frozen after that disclosure and before their outputs were
computed in this repository:

- adaptive-ODE versus fixed-grid convergence;
- every matrix-log branch diagnostic;
- random gauge-rephasing invariance;
- 256 perturbation draws with a fixed seed;
- shot-cost calculation;
- the independent weak-drive analytic construction;
- its finite-difference validation at three drive scales;
- the held-out distance scan and `r^-6` slope; and
- all zero-interaction, equal-mask, single-kick, palindrome, and reversed-
  schedule controls.

The adversarial literature audit was already negative for broad novelty before
the validation run.  Thus no positive numerical outcome can change the A-star
verdict of this branch.

