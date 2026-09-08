"""Local quantum-channel and finite-measurement benchmark; no QPU/API calls."""
from __future__ import annotations
from pathlib import Path
import json
import sys
import time
import numpy as np
from scipy.optimize import minimize
from scipy.linalg import eigh
from scipy.stats import beta as beta_distribution

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / 'results/pauli_fourth_moment_phase0'
sys.path.insert(0, str(ROOT / 'experiments/pauli_fourth_moment_phase0'))
I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], complex)
Y = np.array([[0, -1j], [1j, 0]], complex)
Z = np.diag([1., -1.]).astype(complex)
METHODS = ('ideal_beta', 'noisy_beta', 'noisy_score')
NAMES = ('G8', 'antiC7', 'G9', 'antiC9', 'C009', 'C014')
NOISE = (('none', 0.), ('depolarizing', .003), ('depolarizing', .01),
         ('amplitude_damping', .01), ('amplitude_damping', .03))
SHOTS = (10000, 1000000, 10000000)
DELTA = .01 / (720 * 3 * 3)


def load(name):
    return json.loads((OLD / name).read_text(encoding='utf-8'))


def word_labels(words):
    q = len(words[0])
    return [(sum(1 << (q-1-j) for j, c in enumerate(w) if c in 'XY'),
             sum(1 << (q-1-j) for j, c in enumerate(w) if c in 'YZ')) for w in words], q


def edges_for(labels):
    return {(i, j) for i, (x, z) in enumerate(labels)
            for j, (xx, zz) in enumerate(labels) if i < j and
            ((x & zz).bit_count() + (z & xx).bit_count()) % 2}


def stable_bound(n, edges, weights):
    neighbors = [sum(1 << j for j in range(n) if tuple(sorted((i, j))) in edges) for i in range(n)]
    def visit(todo, value):
        if not todo:
            return value
        bit = todo & -todo
        i = bit.bit_length()-1
        return max(visit(todo ^ bit, value),
                   visit(todo & ~bit & ~neighbors[i], value + weights[i]))
    return visit((1 << n)-1, 0)


def system(name):
    import networkx as nx
    from run_scf_hbar_falsification import standard_saur
    if name == 'G8':
        old = load('almost_clique_closure_counterexample.json')
        labels, q = word_labels(old['pauli_words'])
        w = old['weights']; role = 'development'
    elif name == 'G9':
        labels, q = word_labels(['XIII', 'IXII', 'IIXI', 'ZIII', 'IZII', 'ZZZI', 'YZYX', 'YYXX', 'YXZZ'])
        w = [1]*7 + [2, 2]; role = 'held_out'
    elif name in ('antiC7', 'antiC9'):
        n = 7 if name == 'antiC7' else 9
        labels, q = standard_saur(nx.complement(nx.cycle_graph(n)))
        w = [1]*n; role = 'development' if n == 7 else 'held_out'
    elif name == 'C009':
        labels, q = standard_saur(nx.from_graph6_bytes(b'K{S{aSfF~Fln'))
        w = [1]*9 + [2]*3; role = 'proved_negative_control'
    elif name == 'C014':
        old = load('scf_two_xx_weight_c014.json')
        labels, q = old['standard_SAUR_labels'], 7
        w = old['records'][0]['weights']; role = 'open_stress'
    else:
        raise ValueError(name)
    edges = edges_for(labels)
    return dict(name=name, labels=[list(v) for v in labels], qubits=q,
                weights=w, bound=stable_bound(len(labels), edges, w), role=role)


def frame(labels, q, index):
    values = [list(v) for v in labels]
    gates = []
    if index:
        rng = np.random.default_rng(910000 + 100*q + index)
        for _ in range(4*q):
            gate = int(rng.integers(3)); a = int(rng.integers(q))
            b = (a + int(rng.integers(1, q))) % q
            gates.append([gate, a, b])
            for v in values:
                x, z = v
                if gate == 0:  # H; discard overall sign, irrelevant to squared objective.
                    if ((x >> a) ^ (z >> a)) & 1:
                        x ^= 1 << a; z ^= 1 << a
                elif gate == 1:
                    z ^= ((x >> a) & 1) << a
                else:
                    x ^= ((x >> a) & 1) << b
                    z ^= ((z >> b) & 1) << a
                v[:] = [x, z]
    assert edges_for(values) == edges_for(labels)
    return values, gates


def operators(labels, q, channel='none', strength=0.):
    p = float(strength)
    local = {(0, 0): I, (1, 0): X, (1, 1): Y, (0, 1): Z}
    result = []
    for x, z in labels:
        mat = np.ones((1, 1), complex)
        for bit in reversed(range(q)):
            key = ((x >> bit) & 1, (z >> bit) & 1)
            a = local[key]
            if key != (0, 0):
                if channel == 'depolarizing':
                    a = (1-p)*a
                elif channel == 'amplitude_damping':
                    a = (1-p)*Z+p*I if key == (0, 1) else np.sqrt(1-p)*a
                elif channel != 'none':
                    raise ValueError(channel)
            mat = np.kron(mat, a)
        result.append(mat)
    return np.stack(result)


def density_channel(state, q, channel, strength):
    """Independent block/Kraus Schrödinger implementation, no dressed operators."""
    state = np.asarray(state, complex)
    if abs(np.vdot(state, state).real-1) > 1e-9:
        raise ValueError('State is not normalized')
    rho = np.outer(state, state.conj())
    p = strength
    for bit in range(q):
        zero = np.array([j for j in range(1 << q) if not (j >> bit & 1)])
        one = zero | (1 << bit)
        if channel == 'amplitude_damping':
            d = np.ones(1 << q); d[one] = np.sqrt(1-p)
            out = d[:, None]*rho*d[None, :]
            out[np.ix_(zero, zero)] += p*rho[np.ix_(one, one)]
        elif channel == 'depolarizing':
            partial = rho[np.ix_(zero, zero)] + rho[np.ix_(one, one)]
            out = (1-p)*rho
            out[np.ix_(zero, zero)] += p*partial/2
            out[np.ix_(one, one)] += p*partial/2
        elif channel == 'none':
            out = rho
        else:
            raise ValueError(channel)
        rho = out
    assert abs(np.trace(rho)-1) < 1e-9
    assert np.max(abs(rho-rho.conj().T)) < 1e-9
    assert np.linalg.eigvalsh(rho)[0] > -1e-9
    return rho


def density_expectations(rho, labels):
    values = []
    for x, z in labels:
        phase = 1j**((x & z).bit_count() % 4)
        value = sum(rho[j, j ^ x]*phase*(-1 if (j & z).bit_count() % 2 else 1)
                    for j in range(len(rho)))
        assert abs(value.imag) < 1e-9
        values.append(value.real)
    return np.array(values)


def moments(ops, psi):
    applied = ops @ psi
    return np.real(applied @ psi.conj()), applied


def score_and_gradient(raw, ops, w, bound, score=True):
    dim = len(raw)//2
    v = raw[:dim] + 1j*raw[dim:]
    norm = np.linalg.norm(v)
    if norm < 1e-12:
        raise ValueError('Zero trial state')
    psi = v/norm
    mu, applied = moments(ops, psi)
    mu = np.clip(mu, -1, 1)
    f = float(w @ mu**2)
    deriv = 2*w*mu
    if score:
        rad = np.sqrt(np.maximum(mu**2*(1-mu**2), 0) + 1e-12)
        denom = float(2*w @ rad) + 1e-8
        dden = 2*w*mu*(1-2*mu**2)/rad
        deriv = (deriv*denom-(f-bound)*dden)/denom**2
        value = (f-bound)/denom
    else:
        value = f
    direction = deriv @ applied
    projected = 2*(direction-psi*np.vdot(psi, direction).real)/norm
    return float(value), np.r_[projected.real, projected.imag]


class BudgetReached(Exception):
    pass


def optimize(method, original, dressed, weights, bound, seed, seconds=3., starts_cap=512):
    start = time.monotonic(); deadline = start+seconds
    rng = np.random.default_rng(seed)
    w = np.asarray(weights, float)
    dim = original.shape[1]
    ops = original if method == 'ideal_beta' else dressed
    best = None; evaluations = 0; restarts = 0; converged = 0; fallback = 0
    def record(psi):
        nonlocal best, evaluations
        evaluations += 1
        raw = np.r_[psi.real, psi.imag]
        val, grad = score_and_gradient(raw, ops, w, bound, method == 'noisy_score')
        if best is None or val > best[0]:
            best = (val, psi.copy())
        return val, grad
    def see_saw(psi, iterations):
        nonlocal converged, fallback
        for _ in range(iterations):
            if time.monotonic() >= deadline:
                raise BudgetReached
            record(psi)
            mu, _ = moments(ops, psi)
            H = np.tensordot(w*mu, ops, axes=1)
            try:
                ev, U = np.linalg.eigh(H)
            except np.linalg.LinAlgError:
                ev, U = eigh(H, driver='evr'); fallback += 1
            idx = int(np.argmax(abs(ev))); new = U[:, idx]
            assert np.linalg.norm(H@new-ev[idx]*new) < 1e-8
            distance = 1-abs(np.vdot(new, psi))
            psi = new
            record(psi)
            if distance < 1e-10:
                converged += 1; break
        return psi
    try:
        while restarts < starts_cap:
            if time.monotonic() >= deadline:
                break
            restarts += 1
            psi = rng.normal(size=dim)+1j*rng.normal(size=dim)
            psi /= np.linalg.norm(psi)
            record(psi)
            psi = see_saw(psi, 64 if method == 'noisy_score' else 512)
            if method == 'noisy_score':
                def fun(raw):
                    if time.monotonic() >= deadline:
                        raise BudgetReached
                    v = raw[:dim]+1j*raw[dim:]; v /= np.linalg.norm(v)
                    record(v)
                    val, grad = score_and_gradient(raw, ops, w, bound, True)
                    return -val, -grad
                solved = minimize(fun, np.r_[psi.real, psi.imag], method='L-BFGS-B', jac=True,
                                  options={'maxiter': 512, 'maxfun': 2000, 'ftol': 1e-12, 'gtol': 1e-8})
                converged += int(solved.success)
    except BudgetReached:
        pass
    assert best is not None
    psi = best[1]
    return dict(method=method, state=[[float(z.real), float(z.imag)] for z in psi],
                selection_objective=float(best[0]), optimizer_seconds=time.monotonic()-start,
                restarts=restarts, evaluations=evaluations, converged_local_solves=converged,
                eigensolver_fallbacks=fallback,
                stop='restart_cap' if restarts == starts_cap else 'time_cap')


def allocation(mu, weights, total):
    mu = np.asarray(mu); w = np.asarray(weights)
    m = len(mu)
    if total < 2*m:
        raise ValueError('Budget below two per observable')
    a = 2*w*np.sqrt(np.maximum(mu**2*(1-mu**2), 0)+1e-12)
    if a.sum() == 0:
        a = np.ones(m)
    extra = (total-2*m)*a/a.sum()
    n = 2+np.floor(extra).astype(np.int64)
    for i in np.argsort(-(extra-np.floor(extra)), kind='stable')[:int(total-n.sum())]:
        n[i] += 1
    assert int(n.sum()) == total and min(n) >= 2
    return n


def lower_squared_sum(counts, n, weights, delta=DELTA):
    k = np.asarray(counts); n = np.asarray(n)
    m = len(n); tail = delta/(2*m)
    lo = np.zeros(k.shape); hi = np.ones(k.shape)
    nn = np.broadcast_to(n, k.shape)
    mask = k > 0
    lo[mask] = beta_distribution.ppf(tail, k[mask], (nn-k+1)[mask])
    mask = k < nn
    hi[mask] = beta_distribution.ppf(1-tail, (k+1)[mask], (nn-k)[mask])
    low = 2*lo-1; high = 2*hi-1
    square = np.where(low > 0, low**2, np.where(high < 0, high**2, 0))
    assert np.all(np.isfinite(square))
    return square @ np.asarray(weights)


def validate(result, spec, labels, noise, seed, repetitions=256):
    psi = np.array([complex(*v) for v in result['state']])
    mu = density_expectations(density_channel(psi, spec['qubits'], *noise), labels)
    dressed = operators(labels, spec['qubits'], *noise)
    check, _ = moments(dressed, psi)
    error = float(np.max(abs(mu-check)))
    assert error < 1e-9
    ideal, _ = moments(operators(labels, spec['qubits']), psi)
    w = np.asarray(spec['weights']); noisy = float(w@mu**2)
    if spec['role'] == 'proved_negative_control':
        assert noisy <= spec['bound']+1e-8
    rng = np.random.default_rng(seed)
    trials = []
    for total in SHOTS:
        n = allocation(mu, w, total)
        counts = rng.binomial(n, np.clip((mu+1)/2, 0, 1), size=(repetitions, len(mu)))
        lower = lower_squared_sum(counts, n, w)
        successes = int(np.sum(lower > spec['bound']))
        lo = 0 if not successes else float(beta_distribution.ppf(.025, successes, repetitions-successes+1))
        hi = 1 if successes == repetitions else float(beta_distribution.ppf(.975, successes+1, repetitions-successes))
        trials.append(dict(total_shots=total, allocation=n.tolist(), simulations=repetitions,
                           detections=successes, power=successes/repetitions,
                           power_interval_95=[lo, hi], mean_lower_bound=float(lower.mean())))
    result.update(noisy_value=noisy, noisy_excess=noisy-spec['bound'],
                  ideal_value=float(w@ideal**2), noisy_expectations=mu.tolist(),
                  independent_channel_max_error=error, measurements=trials,
                  C014_violation_candidate=spec['name'] == 'C014' and noisy > 6+1e-7)
    return result


def cell(job, seconds=3., repetitions=256):
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        spec = system(job['graph'])
        labels, gates = frame(spec['labels'], spec['qubits'], job['frame'])
        noise = NOISE[job['noise']]
        original = operators(labels, spec['qubits'])
        dressed = operators(labels, spec['qubits'], *noise)
        order = list(METHODS)
        shift = job['rep'] % 3; order = order[shift:]+order[:shift]
        selected = []
        for method in order:
            result = optimize(method, original, dressed, spec['weights'], spec['bound'],
                              9012026+10000*job['index']+METHODS.index(method), seconds)
            selected.append(validate(result, spec, labels, noise,
                                     9022026+10000*job['index']+METHODS.index(method), repetitions))
        return dict(job=job, system=spec, frame_labels=labels, frame_gates=gates,
                    noise=list(noise), results=selected, confidence_delta=DELTA,
                    type='simulation_only', top_novelty_confirmed=False)
