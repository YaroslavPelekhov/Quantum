"""Build four review PDFs in a new output directory; preserve earlier PDFs."""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'output/pdf/prepared_20260910'
BUILD = ROOT / 'tmp/pdfs/prepared_20260910'
PAPERS = [
    ('experiments/evoq_mis/paper','main.tex','gsn_qaoa_mis_manuscript', True),
    ('experiments/evoq_mis_full_qoblib/paper','main.tex','qaoa_mps_cross_backend_rank_reversal_manuscript',False),
    ('experiments/evoq_mis_full_qoblib/paper','supplement.tex','qaoa_mps_cross_backend_rank_reversal_supplement',False),
    ('experiments/pauli_fourth_moment_phase0/paper','main.tex','weighted_pauli_uncertainty_manuscript',False),
]


def run(command, cwd):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, errors='replace',timeout=180)
    if result.returncode:
        print(result.stdout[-7000:] + result.stderr[-1000:])
        raise RuntimeError(str(command))


def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    BUILD.mkdir(parents=True,exist_ok=True)
    records=[]
    for directory, source, name, bibliography in PAPERS:
        cwd = ROOT / directory
        args = ['pdflatex','--disable-installer','-no-shell-escape','-interaction=nonstopmode',
                '-halt-on-error',f'-output-directory={BUILD}',f'-jobname={name}',source]
        run(args,cwd)
        if bibliography:
            run(['bibtex',str(BUILD/name)],cwd)
        run(args,cwd)
        run(args,cwd)
        pdf=OUTPUT/(name+'.pdf')
        pdf.write_bytes((BUILD/(name+'.pdf')).read_bytes())
        log=(BUILD/(name+'.log')).read_text(errors='replace')
        warnings=[s for s in log.splitlines() if any(x in s for x in ('Overfull','undefined','multiply defined'))]
        records.append(dict(pdf=str(pdf.relative_to(ROOT)), warnings=warnings))
        print(name, warnings, flush=True)
    (ROOT/'research_package/results/build.json').write_text(json.dumps(records,indent=2)+'\n')


if __name__ == '__main__':
    main()
