"""Post-run audit, no optimization; independent dense Kraus and interval code.

Shares NumPy/SciPy and the specified RNG with discovery, not an external
reproduction. Saved outcomes are replayed; optimizer trajectories are not.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from scipy.special import betaincinv
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
METHODS = ('ideal_beta', 'noisy_beta', 'noisy_score')
NAMES = ('G8', 'antiC7', 'G9', 'antiC9', 'C009', 'C014')
NOISE = (('none', 0.), ('depolarizing', .003), ('depolarizing', .01),
         ('amplitude_damping', .01), ('amplitude_damping', .03))
SHOTS = (10000, 1000000, 10000000)
DELTA = .01/(720*3*3)
I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], complex)
Y = np.array([[0, -1j], [1j, 0]], complex)
Z = np.diag([1., -1.]).astype(complex)


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def close(a, b, tol=1e-9):
    assert np.all(np.isfinite(a)) and np.all(np.isfinite(b))
    error = float(np.max(np.abs(np.asarray(a)-np.asarray(b))))
    assert error <= tol, (error, tol)
    return error


def tensor(factors):
    out = np.ones((1, 1), complex)
    for factor in factors:
        out = np.kron(out, factor)
    return out


def dense_paulis(labels, q):
    lookup = {(0, 0): I, (1, 0): X, (0, 1): Z, (1, 1): Y}
    return np.array([tensor([lookup[(x >> j & 1, z >> j & 1)]
                            for j in reversed(range(q))]) for x, z in labels])


def kraus_maps(q, channel, p):
    if channel == 'none':
        return []
    local = ([np.diag([1., np.sqrt(1-p)]), np.array([[0., np.sqrt(p)], [0., 0.]])]
             if channel == 'amplitude_damping' else
             [np.sqrt(1-3*p/4)*I, np.sqrt(p/4)*X, np.sqrt(p/4)*Y, np.sqrt(p/4)*Z])
    assert channel in ('amplitude_damping', 'depolarizing')
    return [[tensor([k if j == bit else I for j in reversed(range(q))]) for k in local]
            for bit in range(q)]


def evolve(psi, maps):
    close(np.vdot(psi, psi), 1.)
    rho = np.outer(psi, psi.conj())
    for local in maps:
        rho = sum(k@rho@k.conj().T for k in local)
    close(np.trace(rho), 1.)
    close(rho, rho.conj().T)
    assert np.linalg.eigvalsh(rho)[0] >= -1e-9
    return rho


def interval(k, n, tail):
    k, n = np.broadcast_arrays(k, n)
    lo = np.zeros(k.shape); hi = np.ones(k.shape)
    mask = k > 0
    lo[mask] = betaincinv(k[mask], n[mask]-k[mask]+1, tail)
    mask = k < n
    hi[mask] = betaincinv(k[mask]+1, n[mask]-k[mask], 1-tail)
    return lo, hi


def lower(k, n, w):
    lo, hi = interval(k, n, DELTA/(2*len(w)))
    left, right = 2*lo-1, 2*hi-1
    dist = np.maximum(np.maximum(left, -right), 0.)
    return dist**2 @ w


def allocate(mu, w, total):
    importance = 2*w*np.sqrt(np.maximum(mu**2*(1-mu**2), 0.)+1e-12)
    amounts = (total-2*len(w))*importance/importance.sum()
    floor = np.floor(amounts).astype(int)
    order = sorted(range(len(w)), key=lambda i: (-(amounts[i]-floor[i]), i))
    for i in order[:int(total-2*len(w)-sum(floor))]:
        floor[i] += 1
    return floor+2


def verify(out, seconds=600):
    start = time.monotonic()
    read = lambda p: json.loads(p.read_text(encoding='utf-8'))
    meta, status = read(out/'metadata.json'), read(out/'status.json')
    assert status['status'] == 'completed' and status['completed_cells'] == 720
    assert not status['errors'] and not meta['pilot'] and not meta['QPU_calls']
    assert not meta['model_api_calls']
    assert digest(HERE/'PROTOCOL.md') == meta['protocol_sha256']
    for name, expected in meta['code_hashes'].items():
        assert digest(HERE/name) == expected, name
    for name, expected in meta['source_hashes'].items():
        assert digest(ROOT/'results/pauli_fourth_moment_phase0'/name) == expected
    assert digest(ROOT/'experiments/pauli_fourth_moment_phase0/run_scf_hbar_falsification.py') == meta['realization_code_sha256']
    jobs = [dict(index=i, graph=g, frame=f, noise=n, rep=r) for i, (r,n,f,g) in
            enumerate((r,n,f,g) for r in range(8) for n in range(5) for f in range(3) for g in NAMES)]
    assert meta['jobs'] == jobs
    files = sorted((out/'cells').glob('cell_*.json'))
    assert [p.name for p in files] == [f'cell_{i:04d}.json' for i in range(720)]
    groups = defaultdict(list); excess = defaultdict(list); runtimes = defaultdict(list)
    cache = {}; maximum_error = 0.; manifests = {}
    # Explicit controls exercise the new implementation before accepting data.
    close(evolve(np.array([0., 1.]), kraus_maps(1, 'amplitude_damping', .2)), np.diag([.2, .8]))
    close(evolve(np.array([0., 1.]), kraus_maps(1, 'depolarizing', .2)), np.diag([.1, .9]))
    close(dense_paulis([(1, 1)], 1)[0], Y)
    assert lower(np.array([[5]]), np.array([10]), np.array([1.]))[0] == 0
    for path, job in zip(files, jobs):
        assert time.monotonic()-start < seconds, 'audit time cap; no completed verdict'
        row = read(path); assert row['job'] == job and not row.get('error')
        assert row['confidence_delta'] == DELTA and not row['top_novelty_confirmed']
        spec = row['system']; q = spec['qubits']; w = np.array(spec['weights'])
        assert spec['name'] == job['graph'] and tuple(row['noise']) == NOISE[job['noise']]
        key = (job['graph'], job['frame'], job['noise'])
        if key not in cache:
            cache[key] = (dense_paulis(row['frame_labels'], q), kraus_maps(q, *row['noise']), spec, row['frame_labels'])
        ops, maps, expected_spec, expected_labels = cache[key]
        assert spec == expected_spec and row['frame_labels'] == expected_labels
        assert {r['method'] for r in row['results']} == set(METHODS) and len(row['results']) == 3
        for result in row['results']:
            method = result['method']; psi = np.array([complex(*z) for z in result['state']])
            assert len(psi) == 2**q
            rho = evolve(psi, maps)
            mu = np.einsum('aij,ji->a', ops, rho).real
            maximum_error = max(maximum_error, close(mu, result['noisy_expectations']))
            value = float(w@mu**2); close(value, result['noisy_value'])
            close(value-spec['bound'], result['noisy_excess'])
            ideal = np.real(np.einsum('i,aij,j->a', psi.conj(), ops, psi))
            close(w@ideal**2, result['ideal_value'])
            excess[job['graph']].append(value-spec['bound'])
            assert result['C014_violation_candidate'] == (job['graph'] == 'C014' and value > 6+1e-7)
            if job['graph'] == 'C009':
                assert value <= 3+1e-8
            assert result['independent_channel_max_error'] < 1e-9
            assert 1 <= result['restarts'] <= 512
            runtimes[method].append(result['optimizer_seconds'])
            rng = np.random.default_rng(9022026+10000*job['index']+METHODS.index(method))
            assert [t['total_shots'] for t in result['measurements']] == list(SHOTS)
            # Replay uses archived means after independent channel comparison;
            # this preserves the exact RNG path despite last-bit roundoff.
            stored_mu = np.array(result['noisy_expectations'])
            for trial in result['measurements']:
                total = trial['total_shots']; n = allocate(stored_mu, w, total)
                assert n.tolist() == trial['allocation'] and trial['simulations'] == 256
                counts = rng.binomial(n, np.clip((stored_mu+1)/2, 0, 1), size=(256, len(w)))
                lows = lower(counts, n, w)
                hits = int(sum(lows > spec['bound']))
                assert hits == trial['detections'] and trial['power'] == hits/256
                close(lows.mean(), trial['mean_lower_bound'], 1e-8)
                l, h = interval(np.array(hits), np.array(256), .025)
                close([float(l), float(h)], trial['power_interval_95'])
                groups[(job['graph'], row['noise'][0], total, method)].append(hits/256)
        manifests[path.name] = digest(path)
        if (job['index']+1) % 120 == 0:
            print(f'verified {job["index"]+1}/720', flush=True)
    held = []
    for graph in ('G9', 'antiC9'):
        for total in SHOTS:
            powers = {m: float(np.mean(groups[graph, 'amplitude_damping', total, m])) for m in METHODS}
            assert all(len(groups[graph, 'amplitude_damping', total, m]) == 48 for m in METHODS)
            held.append(dict(graph=graph, shots=total, cells_per_method=48, mean_power=powers,
                             gain_vs_ideal=powers['noisy_score']-powers['ideal_beta'],
                             gain_vs_noisy=powers['noisy_score']-powers['noisy_beta']))
    passes = [n for n in SHOTS if all(r['gain_vs_ideal'] >= .1 and r['gain_vs_noisy'] >= .1 for r in held if r['shots'] == n)]
    return dict(status='verified', cells=720, selected_states=2160, measurement_replays=6480,
                channel_max_error=maximum_error, held_out=held, passing_budgets=passes,
                empirical_gate='PASS_FOLLOWUP_ONLY' if passes else 'FAIL',
                max_excess={g:max(v) for g,v in excess.items()},
                optimizer_seconds={m:dict(min=min(v),max=max(v),mean=float(np.mean(v)), above_3_01=sum(t>3.01 for t in v)) for m,v in runtimes.items()},
                elapsed_seconds=time.monotonic()-start, cell_hashes=manifests,
                limitations=['Same-host post-run audit, not independent hardware validation.',
                             'Shared NumPy/SciPy/RNG; optimizer trajectories not replayed.',
                             'Observable source and graph bounds rely on frozen prior certificates; not reproved here.',
                             'All three budgets reported; no positive multiplicity-adjusted claim.',
                             'No A-star novelty confirmation.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--campaign', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Do not overwrite an earlier audit'
    with threadpool_limits(limits=1):
        audit = verify(args.campaign)
    args.output.write_text(json.dumps(audit, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k != 'cell_hashes'}, indent=2))
