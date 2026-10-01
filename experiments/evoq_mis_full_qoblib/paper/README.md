# Paper build

The manuscript is an advisor-ready research draft centered on
observable-level certification of MPS schedule rankings. It includes a frozen
five-case, 300-row Aer/cuTensorNet exact replication and the motivating
55-qubit truncation-induced rank reversal. It does not claim that the selected
schedule is universally superior, that the 55-qubit state was simulated
exactly, or that the correlated setting cohorts are independent population
samples.

Build and validate both documents from the repository root:

```powershell
python experiments/evoq_mis_full_qoblib/paper/build.py
```

Stable deliverables are
`output/pdf/qaoa_mps_rank_certification_manuscript.pdf` and
`output/pdf/qaoa_mps_rank_certification_supplement.pdf`. The build performs two
LaTeX passes per document and rejects overfull boxes, unresolved references,
undefined citations, and multiply defined labels.

Render for visual QA:

```powershell
pdftoppm -png -r 140 output/pdf/qaoa_mps_rank_certification_manuscript.pdf tmp/pdfs/render/page
pdftoppm -png -r 140 output/pdf/qaoa_mps_rank_certification_supplement.pdf tmp/pdfs/supplement-render/page
```
