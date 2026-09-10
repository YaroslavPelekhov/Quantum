"""Record reproducibility checks without rerunning optimization campaigns."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--math-python', required=True)
    parser.add_argument('--qaoa-python', required=True)
    args = parser.parse_args()
    math = Path(args.math_python).resolve()
    qaoa = Path(args.qaoa_python).resolve()
    phase = ROOT / 'experiments/pauli_fourth_moment_phase0'
    commands = [
        ('qaoa_integrity', qaoa, ROOT / 'experiments/evoq_mis_full_qoblib', ['-m','unittest','discover','-p','test_*.py']),
        ('gsn_integrity', qaoa, ROOT / 'experiments/evoq_mis', ['-m','unittest','-v','test_qaoa_mis.py']),
        ('readiness_integrity', qaoa, HERE, ['-m','unittest','discover','-v','-p','test_*.py']),
        ('pauli_full_suite', math, ROOT, ['-m','unittest','discover','-s',str(phase),'-p','test_*.py']),
    ]
    for script in ('verify_scf_rectangular_gram_bridge.py', 'verify_scf_core_refinement.py',
                   'verify_scf_three_row_gram.py', 'verify_scf_d_closure.py',
                   'verify_c031_exact_six.py', 'verify_c038_line_graph_hbar.py',
                   'paper/check_paper.py'):
        commands.append((Path(script).stem, math, ROOT, ['-S',str(phase / script)]))
    output = HERE / 'results'
    output.mkdir(exist_ok=True)
    records = []
    for name, python, cwd, argv in commands:
        start = time.monotonic()
        run = subprocess.run([str(python), *argv], cwd=cwd, capture_output=True,
                             text=True, encoding='utf-8', errors='replace', timeout=1200)
        log = run.stdout + '\n' + run.stderr
        (output / f'{name}.log').write_text(log, encoding='utf-8')
        records.append(dict(name=name, command=[str(python), *argv], cwd=str(cwd),
                            exit_code=run.returncode, seconds=time.monotonic()-start,
                            log_sha256=hashlib.sha256(log.encode()).hexdigest(),
                            log_file=f'{name}.log'))
        payload = dict(complete=False, all_passed=all(r['exit_code']==0 for r in records), checks=records)
        (output/'validation.json').write_text(json.dumps(payload, indent=2)+'\n',encoding='utf-8')
        print(f'{name}: exit={run.returncode}, seconds={records[-1]["seconds"]:.3f}', flush=True)
    payload['complete'] = True
    (output/'validation.json').write_text(json.dumps(payload, indent=2)+'\n',encoding='utf-8')
    if not payload['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
