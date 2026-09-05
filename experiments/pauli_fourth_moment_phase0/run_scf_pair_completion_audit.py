"""Adversarial test of a proposed correlation-based separator completion.

The exploratory proposal is y_ij=max(0,(r_i^2+r_j^2+r_ij^2-1)/2).
Any failure concerns this proposal, not hbar-perfectness. Discovered
separators are independently checked on rational profiles and all vertices.
"""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import itertools
import json
from pathlib import Path
import networkx as nx
import numpy as np
from scipy.optimize import linprog
from run_scf_exact_facet_census import stable_masks
from run_scf_hbar_falsification import matrices_for_graph, standard_saur, I, X, Y, Z, is_scf


def profile(operators, vector, pairs):
    norm = int(np.vdot(vector, vector).real)
    numerators = [np.vdot(vector, op@vector) for op in operators]
    assert all(abs(x.imag) < 1e-8 and abs(x.real-round(x.real)) < 1e-8 for x in numerators)
    r = [F(round(x.real), norm) for x in numerators]
    x = [a*a for a in r]
    q = []
    for i, j in pairs:
        numerator = np.vdot(vector, operators[i]@operators[j]@vector)
        assert abs(numerator.imag) < 1e-8 and abs(numerator.real-round(numerator.real)) < 1e-8
        q.append(F(round(numerator.real), norm))
    y = [max(F(0), (x[i]+x[j]+a*a-1)/2) for (i, j), a in zip(pairs, q)]
    return x+y, r, q


def lifted_vertices(graph, pairs):
    n = len(graph)
    return [[(mask >> i) & 1 for i in range(n)]+[
             int(bool(mask >> i & 1 and mask >> j & 1)) for i, j in pairs]
            for mask in stable_masks(graph)]


def separate(vertices, point):
    d = len(point)
    # max a.point-b subject to a.vertex<=b and |a_i|<=1.
    result = linprog([-float(x) for x in point]+[1.],
        A_ub=[v+[-1] for v in vertices], b_ub=np.zeros(len(vertices)),
        bounds=[(-1, 1)]*d+[(None, None)], method='highs')
    assert result.success
    if result.fun >= -1e-8:
        return None
    a = [F(float(x)).limit_denominator(1_000_000) for x in result.x[:-1]]
    bound = max(sum(c*v for c, v in zip(a, vertex)) for vertex in vertices)
    value = sum(c*x for c, x in zip(a, point))
    assert value > bound
    return {'coefficients': list(map(str, a)), 'exact_vertex_bound': str(bound),
            'exact_proposed_lift_value': str(value), 'exact_gap': str(value-bound)}


def audit_graph(graph, pairs, vectors, label):
    operators = matrices_for_graph(graph)
    vertices = lifted_vertices(graph, pairs)
    for trial, vector in enumerate(vectors(operators.shape[1])):
        point, r, q = profile(operators, vector, pairs)
        witness = separate(vertices, point)
        if witness:
            return {'label': label, 'graph6': nx.to_graph6_bytes(graph, header=False).decode().strip(),
                    'pairs': [list(p) for p in pairs], 'trial': trial, 'tested': trial+1,
                    'pauli_binary_labels': [list(p) for p in standard_saur(graph)[0]],
                    'integer_state_real': np.real(vector).astype(int).tolist(),
                    'integer_state_imag': np.imag(vector).astype(int).tolist(),
                    'state_norm_squared': int(np.vdot(vector, vector).real),
                    'expectations': list(map(str, r)), 'pair_product_expectations': list(map(str, q)),
                    'proposed_lift': list(map(str, point)), 'separator': witness,
                    'status': 'canonical_pair_completion_falsified'}
    return {'label': label, 'tested': trial+1, 'status': 'no_failure_in_bounded_samples'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--samples', type=int, default=128)
    args = parser.parse_args()
    rng = np.random.default_rng(9062026)

    def vectors(dimension):
        for _ in range(args.samples):
            vector = rng.integers(-3, 4, dimension)+1j*rng.integers(-3, 4, dimension)
            if np.vdot(vector, vector).real:
                yield vector

    rows = []
    for record in json.loads(args.input.read_text())['records']:
        graph = nx.from_graph6_bytes(record['graph6'].encode())
        pairs = [p for p in itertools.combinations(record['separator'], 2) if not graph.has_edge(*p)]
        row = audit_graph(graph, pairs, vectors, f"residual_{record['representative_index']}_separator")
        rows.append(row)
        print(json.dumps({k: row[k] for k in ('label', 'tested', 'status')}), flush=True)
    # A separate exact analytic control uses the full two-qubit Pauli graph.
    operators = np.asarray([np.kron(a, b) for a, b in itertools.product([I, X, Y, Z], repeat=2)][1:])
    graph = nx.Graph()
    graph.add_nodes_from(range(15))
    graph.add_edges_from((i, j) for i, j in itertools.combinations(range(15), 2)
                        if np.linalg.norm(operators[i]@operators[j]+operators[j]@operators[i]) < 1e-8)
    assert is_scf(graph)
    pairs = [p for p in itertools.combinations(range(15), 2) if not graph.has_edge(*p)]
    vector = np.array([1, 2, 3, 4], dtype=complex)
    point, r, q = profile(operators, vector, pairs)
    vertices = lifted_vertices(graph, pairs)
    coefficients = [2]*15+[-1]*len(pairs)
    bound = max(sum(a*v for a, v in zip(coefficients, vertex)) for vertex in vertices)
    value = sum(F(a)*v for a, v in zip(coefficients, point))
    assert bound == 3 and value == F(179, 50)
    control = {'graph': 'full_two_qubit_Pauli_graph_G15', 'SCF': True,
               'graph6': nx.to_graph6_bytes(graph, header=False).decode().strip(),
               'pauli_binary_labels': [[a[0]+2*b[0], a[1]+2*b[1]] for a, b in itertools.product(
                   [(0,0),(1,0),(1,1),(0,1)], repeat=2)][1:],
               'integer_state_real': [1,2,3,4], 'integer_state_imag': [0,0,0,0],
               'proposed_lift': list(map(str, point)),
               'state': '(1,2,3,4)/sqrt(30)', 'pairs': len(pairs),
               'sum_squared_expectations': str(sum(point[:15])),
               'sum_proposed_pair_probabilities': str(sum(point[15:])),
               'valid_lift_inequality': '2 sum_i x_i - sum_nonedge_ij y_ij <= 3',
               'exact_value': str(value), 'exact_bound': 3, 'exact_violation': str(value-3),
               'vertices_checked': len(vertices),
               'scope': 'all-pairs completion; not by itself a two-clique-separator counterexample'}
    payload = {'experiment': 'correlation_based_canonical_pair_completion_falsification',
               'seed': 9062026, 'samples_cap_per_separator': args.samples,
               'state_samples_tested': sum(r['tested'] for r in rows),
               'proposal': 'y_ij=max(0,(r_i^2+r_j^2+r_ij^2-1)/2)',
               'separator_cases': len(rows), 'separator_failures': sum('separator' in r for r in rows),
               'quantum_hbar_claim_falsified': False, 'records': rows, 'exact_G15_control': control}
    args.output.write_text(json.dumps(payload, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
