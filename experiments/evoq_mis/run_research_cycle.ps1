$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$workspace = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$python = Join-Path $workspace ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing experiment Python environment: $python"
}

Push-Location $workspace
try {
    & $python -m unittest discover -s .\experiments\evoq_mis -p "test_*.py" -v
    & $python .\experiments\evoq_mis\run_experiment.py --budget 60 --shots 4096 --trials 8 --noise-shots 256 --noise-trials 4 --search-repeats 12 --p 1 --seed 20260802
    & $python .\experiments\evoq_mis\run_p2_pareto.py --budget 300 --repeats 12 --shots 4096 --shot-trials 8 --noise-shots 256 --noise-trials 4 --seed 20260802
    & $python .\experiments\evoq_mis\evaluate_p2_transfer.py
    & $python .\experiments\evoq_mis\run_multitask_normalized.py --budget 300 --repeats 12 --seed 20260802 --shots 4096 --shot-trials 8 --noise-shots 256 --noise-trials 4
    & $python .\experiments\evoq_mis\run_feasible_mixer.py --budget 300 --repeats 12 --seed 20260803 --shots 4096 --shot-trials 8
    & $python .\experiments\evoq_mis\run_objective_ablation.py
    & $python .\experiments\evoq_mis\run_scaleup_audit.py
    & $python .\experiments\evoq_mis\run_hardware_audit.py
    & $python .\experiments\evoq_mis\run_confirmatory.py
    & $python .\experiments\evoq_mis\run_random_subset_robustness.py
    & $python .\experiments\evoq_mis\run_classical_sanity.py
    & $python .\experiments\evoq_mis\run_metriq_lrqaoa_local.py
    & $python .\experiments\evoq_mis\paper\build_paper_assets.py
    & $python .\experiments\evoq_mis\build_manifest.py
}
finally {
    Pop-Location
}
