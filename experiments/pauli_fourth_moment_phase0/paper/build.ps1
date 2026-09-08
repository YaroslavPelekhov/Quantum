$ErrorActionPreference = 'Stop'
$paperRoot = $PSScriptRoot
$repoRoot = (Resolve-Path (Join-Path $paperRoot '../../..')).Path
$pdfOutput = Join-Path $repoRoot 'output/pdf'
$latexOutput = Join-Path $repoRoot 'tmp/pdfs/scf-paper-build'
New-Item -ItemType Directory -Force -Path $pdfOutput, $latexOutput | Out-Null
python -S (Join-Path $paperRoot 'check_paper.py')
if ($LASTEXITCODE -ne 0) { throw 'Paper ledger verification failed.' }
Push-Location $paperRoot
try {
    for ($pass = 1; $pass -le 2; $pass++) {
        & pdflatex --disable-installer -no-shell-escape -interaction=nonstopmode -halt-on-error "-output-directory=$latexOutput" '-jobname=weighted_pauli_uncertainty_manuscript' 'main.tex'
        if ($LASTEXITCODE -ne 0) { throw "LaTeX pass $pass failed." }
    }
    Copy-Item -LiteralPath (Join-Path $latexOutput 'weighted_pauli_uncertainty_manuscript.pdf') -Destination $pdfOutput
} finally {
    Pop-Location
}
Write-Output (Join-Path $pdfOutput 'weighted_pauli_uncertainty_manuscript.pdf')
