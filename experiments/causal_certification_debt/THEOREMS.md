# Causal Certification Debt

## Definitions and orientation

The backward sweep stores checkpoints `t=1,...,T`; a local residual compression
performed at checkpoint `j` affects every earlier backward checkpoint `t<=j`.
For residual basis vector `k`, let the certified local increment be

`e_(k,j) = delta_(k,j) + nu_(k,j) >= 0`,

where `delta` is the TT-SVD discarded-norm bound and `nu` is the explicit
floating-point allowance. The scalar tail is

`xi_(k,t) = sum_(j>=t) e_(k,j)`.

Let `a_t>=0` be the certified forward trace-norm sensitivity used by COT.

## Theorem 1: causal certification debt identity

Define

`D = sum_(t,k) a_t xi_(k,t)`

and the causal price

`Lambda_j = sum_(t<=j) a_t`.

Then

`D = sum_(j,k) Lambda_j e_(k,j)`.

Proof: substitute the tail recurrence and exchange two finite nonnegative sums:

`sum_(t,k) a_t sum_(j>=t)e_(k,j)
 = sum_(j,k)e_(k,j)sum_(t<=j)a_t`.

For another indexing convention, `t<=j` is replaced by the corresponding
causal-predecessor relation. On a general backward DAG,
`Lambda_j=sum_(t: t precedes j)a_t`.

## Rank-r and capped observable variant

The implemented rank-`r` observable enclosure is

`eta_t = sum_k min(1, x_(k,t)+xi_(k,t))`,

where `x_(k,t)=||rhat_(k,t)||_2`. It has the exact decomposition

`eta_t = eta_t^rep + eta_t^tail`,

`eta_t^rep = sum_k min(1,x_(k,t))`,

`eta_t^tail = sum_k [min(1,x_(k,t)+xi_(k,t))-min(1,x_(k,t))]`.

Since `u -> min(1,u)` is nondecreasing and 1-Lipschitz,

`0 <= eta_t^tail <= sum_k xi_(k,t)`.

Consequently

`sum_t a_t eta_t
 <= sum_t a_t eta_t^rep + sum_(j,k)Lambda_j e_(k,j)`.

Thus the uncapped causal debt is a valid computable upper budget even when the
production certificate uses rank caps. If no cap is active, equality holds for
the tail component, as in the current ibm32 runs.

## Theorem 2: irreversibility

Every local increment creates guaranteed debt `Lambda_j e_(k,j)>=0`. A later
increase of bond can reduce future increments but cannot subtract this term,
because all subsequent scalar-tail updates are additions of nonnegative values.

This is a property of the certificate recurrence, not an implementation quirk.

## Theorem 3: equal resources do not imply equal certifiability

Consider two placements of local errors `e_h>e_l` at checkpoints with
`Lambda_h>Lambda_l`. Swapping the errors changes debt by

`(Lambda_h-Lambda_l)(e_h-e_l)>0`.

Therefore policies with the same multiset of bond choices, identical maximum
bond, identical average bond, and identical cubic work can have different
certification debt. Causal placement is a necessary resource descriptor.

## Minimum-cost allocation and KKT condition

For trajectories `s`, candidate bonds `b`, local costs `c_(s,j)(b)`, and local
certified increments `e_(s,k,j)(b)`, define the remaining tail budget `B` and
solve

`min sum_(s,j)c_(s,j)(b_(s,j))`

subject to

`sum_(s,j,k)Lambda_(s,j)e_(s,k,j)(b_(s,j)) <= B`.

For differentiable continuous relaxations, every interior active choice obeys

`-Lambda_(s,j)e'_(s,j)(b)/c'_(s,j)(b) = 1/lambda`.

The controller therefore equalizes certified-debt reduction per unit compute,
not discarded weight or fidelity improvement per unit compute. For discrete
bonds this becomes a multiple-choice constrained allocation; the optimization
method is standard, while the causal physical weight `Lambda_j` is the proposed
new primitive.

## Decision Certification Complexity

For instance, competing algorithms `(A,B)`, observable `O`, candidate policy
class `Pi`, and sound certificate `E`, define the operational quantity

`DCC(A,B,O;Pi) = inf_(pi in Pi){C(pi): E_A(pi)+E_B(pi)<|qtilde_A(pi)-qtilde_B(pi)|}`.

This measures the cost of proving a specified decision, not the cost of
globally approximating the quantum state. It is policy-class and implementation
dependent and is not asserted to be a complexity-theory class.
