# Decision-certified bond allocation

This experiment extends COT from one residual bond per comparison to causal,
trajectory-asymmetric residual schedules. It retains a prespecified negative
schedule, a successful secondary causal schedule, and a frozen spectral
transfer that separates soundness transfer from resource-optimality transfer.

```powershell
python experiments/decision_certified_bond_allocation/analyze_bond_allocation.py
python -m unittest experiments.decision_certified_bond_allocation.test_bond_allocation -v
```
