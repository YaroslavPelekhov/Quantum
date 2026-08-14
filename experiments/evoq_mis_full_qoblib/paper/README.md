# Paper build

The manuscript is an advisor-ready research draft centered on
observable-level certification of MPS schedule rankings. It includes a frozen
five-case, 300-row Aer/cuTensorNet exact replication and the motivating
55-qubit truncation-induced rank reversal. It does not claim that the selected
schedule is universally superior, that the 55-qubit state was simulated
exactly, or that the correlated setting cohorts are independent population
samples.

Build from this directory:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf supplement.tex
```

Stable deliverables are
`output/pdf/qaoa_mps_cross_backend_rank_reversal_manuscript.pdf` and
`output/pdf/qaoa_mps_cross_backend_rank_reversal_supplement.pdf`.

Render for visual QA:

```powershell
pdftoppm -png -r 140 output/pdf/main.pdf tmp/pdfs/render/page
pdftoppm -png -r 140 output/pdf/supplement.pdf tmp/pdfs/supplement-render/page
```
