# Frozen shadow-price controller protocol

Locked on 2026-08-21 before the first end-to-end controller execution.

## Controller

At backward checkpoint `j`, compute the causal price

`Lambda_j = sum_(t<=j) a_t`

from certified forward radii. From the current recursively chosen residual
state, evaluate TT-SVD candidates at bonds `{128,256,512}`. For each bond use

`local_debt_j(b) = Lambda_j * sum_k(delta_(k,j)(b) + 1e-10)`

and choose the smallest minimizer of

`score_j(b) = (b/512)^3 + 500 * local_debt_j(b)`.

The only calibrated parameter is the global shadow price `500`. It was chosen
from the already available fixed-bond sorted design ladder before executing the
controller. There are no checkpoint boundaries, no exact-residual inputs, and
no exact BKS/projector errors in selection. Dense vectors remain audit-only.

## Execution order and freeze

1. Execute both ibm32/sorted trajectories as the design evaluation.
2. Without changing the shadow price, candidates, score, or tie rule, execute
   ibm32/spectral.
3. Without changing them, execute a separate QOBLIB graph. A small graph is a
   valid over-allocation control: the controller should choose the cheapest
   candidate whenever all candidate errors are equal to zero.

## Criteria

Sorted primary success requires a correct strict COT ranking certificate and
paired cubic residual work below fixed R256/R256. Spectral and new-graph runs
test transfer; no retuning is permitted after seeing sorted controller output.
All failures and over-allocation are retained.
