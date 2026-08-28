# Frozen sorted design result

The signed decision-gap interval certifies every evaluated adaptive-primary
residual bond from R32 through R512 on `ibm32/confirm/sorted`.  The legacy
absolute-sum COT certificate fails at R32, R64, R96, and R128.

The minimum-cost frozen pair is R32/R32:

- recentered gap: `-0.246122939`;
- paired certified remainder: `0.207303396`;
- strict interval: `[-0.453426335, -0.038819543]`;
- certificate margin: `0.038819543`;
- nominal paired cubic work versus R256/R256: `0.001953125`;
- nominal saving: `99.8046875%`.

The low-bond ladder is path-dependent.  R32 gives a smaller integrated LR
correction (`0.207210800`) than R64 (`0.231992684`), R96 (`0.234152451`), and
R128 (`0.219082433`).  Across audited low-bond checkpoint rows there are zero
dense operator violations.

The frozen R128 `1e-10` repeatability criterion failed: differences from the
archived run are `5.926e-7` for LR and `1.650e-9` for matched-random.  These
differences do not change any verdict but are retained as a numerical
reproducibility limitation.

