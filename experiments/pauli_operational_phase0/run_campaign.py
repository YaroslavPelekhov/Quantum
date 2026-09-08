"""Bounded, checkpointed single-worker campaign. Never launches another campaign."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def stamp():
    return datetime.now(timezone.utc).isoformat()


def atomic(path, value):
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    os.replace(temp, path)


def digest(path):
    raw = path.read_bytes()
    if path.suffix in ('.py', '.md', '.json'):
        raw = raw.replace(b'\r\n', b'\n')
    return hashlib.sha256(raw).hexdigest()


def jobs():
    from engine import NAMES, NOISE
    output = []
    for rep in range(8):
        for noise in range(len(NOISE)):
            for frame in range(3):
                for graph in NAMES:
                    output.append(dict(index=len(output), graph=graph, frame=frame, noise=noise, rep=rep))
    assert len(output) == 720
    return output


def report(out):
    metadata = json.loads((out/'metadata.json').read_text(encoding='utf-8'))
    planned = len(metadata['jobs'])
    groups = {}
    candidates = []
    count = 0
    for file in sorted((out/'cells').glob('cell_*.json')):
        row = json.loads(file.read_text(encoding='utf-8'))
        if row.get('error'):
            continue
        count += 1
        for result in row['results']:
            if result['C014_violation_candidate']:
                candidates.append(dict(file=file.name, method=result['method'], value=result['noisy_value']))
            for trial in result['measurements']:
                key = (row['job']['graph'], row['noise'][0], trial['total_shots'], result['method'])
                groups.setdefault(key, []).append(trial['power'])
    records = [dict(graph=g, channel=c, shots=n, method=m, cells=len(values),
                    mean_power=sum(values)/len(values)) for (g,c,n,m), values in sorted(groups.items())]
    data = dict(completed_paired_cells=count, planned_paired_cells=planned,
                records=records, numerical_C014_candidates=candidates,
                type='simulation_only', top_novelty_confirmed=False,
                warning='Prefix averages may have unequal coverage. Repetitions are not independent graph families.')
    atomic(out/'summary.json', data)
    lines = ['# Operational Pauli campaign: current results', '',
             f'Complete paired cells: {count}/{planned}. Pilot: {metadata["pilot"]}.', '',
             'Local quantum-channel and Bernoulli-measurement simulations only. No QPU data.',
             'No top-novelty claim. Generic significance optimization is established prior art.', '',
             '## Per-family descriptive results', '',
             'Incomplete-prefix averages are not final comparisons; channel strengths and frames are pooled here.',
             'Use the per-cell JSON for all disaggregated results and confidence intervals.', '',
             '| Graph | Channel | Shots | Method | Cells | Mean simulated detection power |',
             '|---|---|---:|---|---:|---:|']
    lines += [f"| {r['graph']} | {r['channel']} | {r['shots']} | {r['method']} | {r['cells']} | {r['mean_power']:.4f} |" for r in records]
    lines += ['', '## Interpretation boundary', '',
              'A higher smoothed optimization score is not a detection result. All methods use the same oracle',
              'allocation rule, and selected states are frozen before independently simulated measurements.',
              'Only G9 and antiC9 are held-out families. C009 is a proved negative control; C014 is open.',
              'No exact counterexample, general quantum theorem, noise-robust deployment or publication priority',
              'is inferred automatically. Inspect PROTOCOL.md and status.json before interpreting partial output.', '',
              '## Sources', '',
              '- Xu et al., beta framework and observable systems: https://arxiv.org/html/2511.13531v1',
              '- Jungnitsch et al., existing significance-optimization principle: https://arxiv.org/abs/0912.0645',
              '- Dirkse et al., correlated-noise inference outside this IID model: https://arxiv.org/abs/2002.12400', '']
    temp = out/'REPORT.md.tmp'; temp.write_text('\n'.join(lines), encoding='utf-8'); os.replace(temp, out/'REPORT.md')
    return data


def run(out, seconds, pilot):
    import psutil
    out = out.resolve()
    if out.exists():
        raise RuntimeError('Use a fresh output directory; no silent overwrite or stale-lock takeover')
    if not pilot:
        dirty = subprocess.check_output(['git', 'status', '--porcelain', '--', str(HERE)], cwd=ROOT, text=True)
        if dirty.strip():
            raise RuntimeError('Commit the frozen campaign source before the held-out campaign')
    out.mkdir(parents=True); (out/'cells').mkdir()
    lock = out/'RUNNING.lock'
    with lock.open('x') as stream:
        stream.write(str(os.getpid()))
    plan = jobs()
    if pilot:
        plan = [plan[0]]  # development G8 only; never tune against held-out outcomes.
    inputs = ['almost_clique_closure_counterexample.json', 'scf_two_xx_weight_c014.json']
    meta = dict(started_utc=stamp(), pid=os.getpid(), pilot=pilot, wall_budget_seconds=seconds,
                commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                code_hashes={p.name:digest(p) for p in HERE.glob('*.py')},
                protocol_sha256=digest(HERE/'PROTOCOL.md'),
                source_hashes={p:digest(ROOT/'results/pauli_fourth_moment_phase0'/p) for p in inputs},
                realization_code_sha256=digest(ROOT/'experiments/pauli_fourth_moment_phase0/run_scf_hbar_falsification.py'),
                preregistration_commit='3237886',
                python=sys.version, versions={p:importlib.metadata.version(p) for p in
                    ('numpy','scipy','networkx','threadpoolctl','psutil')}, jobs=plan,
                type='simulation_only', model_api_calls=False, QPU_calls=False)
    atomic(out/'metadata.json', meta)
    started = time.monotonic(); completed = 0; errors = []
    state = dict(status='running', pid=os.getpid(), started_utc=meta['started_utc'],
                 completed_cells=0, planned_cells=len(plan), wall_budget_seconds=seconds)
    atomic(out/'status.json', state)
    try:
        if os.name == 'nt':
            psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        for job in plan:
            elapsed = time.monotonic()-started
            if elapsed >= seconds or (out/'STOP').exists():
                state['status'] = 'time_cap' if elapsed >= seconds else 'stopped_by_request'
                break
            state.update(active_job=job, elapsed_seconds=elapsed, updated_utc=stamp())
            atomic(out/'status.json', state)
            task = out/'active_job.json'; atomic(task, job)
            dest = out/'cells'/f"cell_{job['index']:04d}.json"
            env = os.environ.copy()
            for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
                env[key] = '1'
            env['PYTHONUNBUFFERED'] = '1'
            args = [sys.executable, str(Path(__file__).resolve()), '--worker', str(task), '--output', str(dest)]
            if pilot:
                args += ['--pilot']
            with (out/'worker.log').open('ab') as log:
                child = subprocess.Popen(args, cwd=ROOT, env=env, stdout=log, stderr=log,
                                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                child_start = time.monotonic(); killed = None
                while child.poll() is None:
                    if time.monotonic()-started >= seconds:
                        killed = 'campaign_time_cap'; child.kill(); break
                    if time.monotonic()-child_start > 90:
                        killed = 'cell_time_cap'; child.kill(); break
                    try:
                        if psutil.Process(child.pid).memory_info().rss > 2*1024**3:
                            killed = 'cell_memory_cap'; child.kill(); break
                    except psutil.NoSuchProcess:
                        pass
                    time.sleep(.25)
                child.wait()
            if killed or child.returncode:
                errors.append(dict(job=job, reason=killed or 'worker_failed', returncode=child.returncode))
                state['status'] = 'time_cap' if killed == 'campaign_time_cap' else 'needs_attention'
                break
            row = json.loads(dest.read_text(encoding='utf-8'))
            assert len(row['results']) == 3
            completed += 1
            state.update(completed_cells=completed, elapsed_seconds=time.monotonic()-started, updated_utc=stamp())
            atomic(out/'status.json', state)
            print(json.dumps(dict(completed_cells=completed, job=job,
                                  values={r['method']:r['noisy_value'] for r in row['results']})), flush=True)
            if completed == 1 or completed % 12 == 0:
                report(out)
            if any(r['C014_violation_candidate'] for r in row['results']):
                state['status'] = 'candidate_requires_exact_review'; break
        else:
            state['status'] = 'completed'
    except Exception as exc:
        state['status'] = 'needs_attention'
        errors.append(dict(error=repr(exc)))
        raise
    finally:
        state.update(completed_cells=completed, elapsed_seconds=time.monotonic()-started,
                     updated_utc=stamp(), errors=errors)
        atomic(out/'status.json', state)
        report(out)
        lock.unlink(missing_ok=True)
    return state


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--seconds', type=float, default=10800)
    p.add_argument('--pilot', action='store_true')
    p.add_argument('--worker', type=Path)
    p.add_argument('--report-only', action='store_true')
    a = p.parse_args()
    if a.report_only:
        report(a.output); return
    if a.worker:
        from engine import cell
        row = cell(json.loads(a.worker.read_text()), seconds=.5 if a.pilot else 3.,
                   repetitions=32 if a.pilot else 256)
        atomic(a.output, row)
    else:
        if not 1 <= a.seconds <= 10800:
            raise ValueError('Wall budget must be in [1,10800] seconds')
        print(json.dumps(run(a.output, a.seconds, a.pilot)), flush=True)


if __name__ == '__main__':
    main()
