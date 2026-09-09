"""C035: nonuniform seed falsification, with every final state retained."""
import json
import time
import numpy as np
import networkx as nx
from threadpoolctl import threadpool_limits
from run_c034_gear_falsification import seeds, stable_bound
from run_scf_two_xx_attack import matrices, optimize
from run_scf_hbar_falsification import standard_saur
from c020_exact_certificate import DATA


def main():
    began = time.monotonic()
    rng = np.random.default_rng(20260911)
    cases, _ = seeds()
    result = dict(experiment='C035_nonuniform_seed_gear', seed=20260911,
                  starts=16, iteration_limit=256, records=[],
                  quantum_transfer_proved=False, status='complete')
    for case, (g, n, endpoints, h6, _) in enumerate(cases):
        h = nx.from_graph6_bytes(h6.encode())
        labels, q = standard_saur(g)
        ops = matrices(labels, q)
        for variant in range(2):
            sw = rng.integers(1, 4, size=n).tolist()
            for v in endpoints:
                sw[v] = 1
            outside = [v for v in range(n) if v not in endpoints]
            w = [sw[v] for v in outside] + [1]*6 + [2]*2
            bound = stable_bound(h, sw) + 2
            actual = stable_bound(g, w)
            r = dict(case=case, variant=variant, seed_graph6=h6,
                     seed_edge=endpoints, seed_weights=sw, weights=w,
                     labels=labels, qubits=q,
                     graph6=nx.to_graph6_bytes(g, header=False).decode().strip(),
                     bound=bound, classical_bound=actual, runs=[])
            if actual != bound:
                r['status'] = 'classical_transfer_failed'
            else:
                r['status'] = 'searched'
                for j in range(result['starts']):
                    initial = np.ones(len(w)) if j == 0 else rng.normal(size=len(w))
                    run = optimize(ops, np.array(w), initial, result['iteration_limit'])
                    # Stationarity of the SAVED best state, not of a later iterate.
                    state = np.array([complex(a,b) for a,b in run['state']])
                    action = np.einsum('i,ijk,k->j', np.array(w)*run['expectations'], ops, state)
                    run['stationarity_residual'] = float(np.linalg.norm(action-run['value']*state))
                    r['runs'].append(run)
            result['records'].append(r)
        print(json.dumps(dict(completed_cases=case+1)), flush=True)
    result['seconds'] = time.monotonic()-began
    return result


if __name__ == '__main__':
    path = DATA/'c035_weighted_gear.json'
    assert not path.exists()
    with threadpool_limits(limits=1):
        report = main()
    with path.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(dict(records=len(report['records']), seconds=report['seconds'])))
