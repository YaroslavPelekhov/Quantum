# Paper build

The manuscript is a conservative research draft centered on the MPS
truncation-induced schedule rank reversal. It does not claim that the selected
schedule is universally superior or that the 55-qubit state was simulated
exactly.

Build from this directory:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory output/pdf supplement.tex
```

Render for visual QA:

```powershell
pdftoppm -png -r 140 output/pdf/main.pdf tmp/pdfs/render/page
pdftoppm -png -r 140 output/pdf/supplement.pdf tmp/pdfs/supplement-render/page
```
