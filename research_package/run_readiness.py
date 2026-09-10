"""Bounded, local-only shot/noise planning. Never connects to a QPU service."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import beta

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXPERIMENT = ROOT / 'experiments/evoq_mis_full_qoblib'
PROTOCOL = HERE / 'shot_noise_protocol.json'
OUT = HERE / 'results'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, payload):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(payload, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def cp_bounds(k, n, alpha):
    k = np.asarray(k)
    lo = beta.ppf(alpha / 2, np.maximum(k, 1), n - k + 1)
    hi = beta.ppf(1 - alpha / 2, k + 1, np.maximum(n - k, 1))
    return np.where(k == 0, 0., lo), np.where(k == n, 1., hi)


def bks_indicator(scorer):
    n = len(scorer['weights'])
    out = np.zeros(2**n, dtype=float)
    for x in range(2**n):
        feasible = not scorer['impossible'] and all((x & mask) != value for mask, value in scorer['forbidden'])
        size = scorer['constant_selected'] + sum(w for i, w in enumerate(scorer['weights']) if (x >> i) & 1)
        out[x] = feasible and size >= scorer['bks']
    return out


def readout_channel(probs, probability):
    out = np.asarray(probs, dtype=float).copy()
    for bit in range(out.size.bit_length() - 1):
        flipped = np.arange(out.size) ^ (1 << bit)
        out = (1 - probability) * out + probability * out[flipped]
    return out


def inputs():
    paths = [EXPERIMENT / 'results/cross_case_replication/export_manifest.json',
             EXPERIMENT / 'results/independent_ladder/export_manifest.json']
    rows = [r for p in paths for r in read(p)['rows']]
    return {(r['case'], r['method'], r['ordering']): r for r in rows}, paths


def shot_experiment(protocol, rows):
    rng = np.random.default_rng(protocol['seed'])
    results = []
    alpha = protocol['family_alpha'] / (2 * protocol['family_comparisons'])
    for case in protocol['cases']:
        refs = [rows[case, method, protocol['ordering']] for method in protocol['methods']]
        p0, p1 = [r['exact_metrics']['bks_rate'] for r in refs]
        sign = np.sign(p1 - p0)
        for n in protocol['shots_per_arm']:
            k0 = rng.binomial(n, p0, protocol['replicates'])
            k1 = rng.binomial(n, p1, protocol['replicates'])
            l0, u0 = cp_bounds(k0, n, alpha)
            l1, u1 = cp_bounds(k1, n, alpha)
            low, high = l1 - u0, u1 - l0
            decision = (low > 0).astype(int) - (high < 0).astype(int)
            resolved = decision != 0
            results.append(dict(case=case, qubits=refs[0]['qubits'], shots_per_arm=n,
                p_lr=p0, p_matched=p1, exact_effect=p1-p0,
                resolved=int(resolved.sum()), wrong_resolved=int(((decision != sign) & resolved).sum()),
                replicates=protocol['replicates'], power_correct=float(np.mean(decision == sign)),
                inconclusive=float(np.mean(~resolved)),
                raw_wrong_sign=float(np.mean(np.sign(k1-k0) == -sign)),
                raw_tie=float(np.mean(k1 == k0))))
    return results


def noise_experiment(protocol, rows):
    import qiskit
    import qiskit_aer
    from qiskit import qpy, transpile
    from qiskit.transpiler import CouplingMap
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error

    compiled_dir = OUT / 'circuits'
    compiled_dir.mkdir(exist_ok=True)
    result = []
    for case in protocol['noise_cases']:
        for method in protocol['methods']:
            row = rows[case, method, protocol['ordering']]
            path = EXPERIMENT / row['circuit_file']
            if digest(path) != row['circuit_sha256']:
                raise ValueError(f'Circuit hash changed: {path}')
            with path.open('rb') as handle:
                circuit, = qpy.load(handle)
            n = circuit.num_qubits
            compiled = transpile(circuit, basis_gates=protocol['basis'],
                coupling_map=CouplingMap.from_line(n), initial_layout=list(range(n)),
                seed_transpiler=protocol['transpile_seed'], optimization_level=protocol['optimization_level'])
            logical_to_physical = compiled.layout.final_index_layout(filter_ancillas=True)
            physical_indices = np.array([sum(((x >> i) & 1) << logical_to_physical[i] for i in range(n)) for x in range(2**n)])
            compiled_path = compiled_dir / f'{case}__{method}__synthetic_line.qpy'
            with compiled_path.open('wb') as handle:
                qpy.dump(compiled, handle)
            indicator = bks_indicator(row['scorer'])
            for p2 in protocol['two_qubit_depolarizing_parameters']:
                noise = NoiseModel()
                p1 = p2 * protocol['one_qubit_parameter_ratio']
                if p2:
                    noise.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ['cx'])
                    noise.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ['sx', 'x'])
                execution = compiled.copy()
                execution.save_probabilities()
                backend = AerSimulator(method='density_matrix', noise_model=noise, max_parallel_threads=2)
                job = backend.run(execution, shots=None).result()
                if not job.success:
                    raise RuntimeError(str(job))
                physical = np.asarray(job.data(0)['probabilities'], dtype=float)
                probs = physical[physical_indices]
                if abs(probs.sum() - 1) > 1e-9 or probs.min() < -1e-10:
                    raise ValueError('Invalid density-matrix probabilities')
                readout = protocol['symmetric_readout_probability_nonzero_noise'] if p2 else 0.
                bks = float(readout_channel(probs, readout) @ indicator)
                exact = row['exact_metrics']['bks_rate']
                if not p2 and abs(bks - exact) > protocol['ideal_tolerance']:
                    raise ValueError(f'Ideal mismatch {case}/{method}: {bks} != {exact}')
                result.append(dict(case=case, method=method, qubits=n, p2=p2, p1=p1,
                    readout=readout, bks_rate=bks, ideal_reference=exact,
                    cx=int(compiled.count_ops().get('cx', 0)), depth=compiled.depth(),
                    final_logical_to_physical=logical_to_physical,
                    circuit_file=str(compiled_path.relative_to(ROOT)), circuit_sha256=digest(compiled_path),
                    scorer=row['scorer']))
                save('noise_checkpoint.json', dict(complete=False, rows=result))
                print(f'noise {case}/{method} p2={p2}: BKS={bks:.9f}', flush=True)
    return result, dict(qiskit=qiskit.__version__, qiskit_aer=qiskit_aer.__version__)


def main():
    protocol = read(PROTOCOL)
    rows, paths = inputs()
    OUT.mkdir(exist_ok=True)
    shots = shot_experiment(protocol, rows)
    save('shot_planning.json', dict(complete=True, protocol_sha256=digest(PROTOCOL), rows=shots))
    noise, versions = noise_experiment(protocol, rows)
    payload = dict(complete=True, timestamp=datetime.now(timezone.utc).isoformat(),
        python=platform.python_version(), numpy=np.__version__, **versions,
        protocol_sha256=digest(PROTOCOL), runner_sha256=digest(Path(__file__)),
        sources={str(p.relative_to(ROOT)): digest(p) for p in paths},
        hardware_submitted=False, synthetic_noise_only=True, shots=shots, noise=noise)
    save('readiness.json', payload)
    save('noise_checkpoint.json', dict(complete=True, rows=noise))
    print('COMPLETE: 25 shot scenarios, 30 exact density-matrix jobs; no QPU jobs.', flush=True)


if __name__ == '__main__':
    main()
