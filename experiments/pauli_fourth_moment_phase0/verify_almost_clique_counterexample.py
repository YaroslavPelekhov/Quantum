"""Exact C003 acceptance: physical state, local all-weight proofs, separator.

Standard library only. The local polytope completeness check enumerates
all full-rank active constraint sets by rational Gaussian elimination,
independently of the discovery engine's double-description algorithm.
"""
from fractions import Fraction as F
import itertools
import json
from pathlib import Path
from verify_scf_generalization import graph_edges, stable, check_scf, apply_pauli, expectation

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def solve_active(rows):
    n = len(rows)
    matrix = [[F(v) for v in row[1:]]+[F(-row[0])] for row in rows]
    assert all(len(row) == n+1 for row in matrix)
    for col in range(n):
        pivot = next((i for i in range(col,n) if matrix[i][col]),None)
        if pivot is None:
            return None
        matrix[col],matrix[pivot] = matrix[pivot],matrix[col]
        scalar = matrix[col][col]
        matrix[col] = [v/scalar for v in matrix[col]]
        for i in range(n):
            if i != col and matrix[i][col]:
                scalar = matrix[i][col]
                matrix[i] = [a-scalar*b for a,b in zip(matrix[i],matrix[col])]
    return tuple(row[-1] for row in matrix)


def induced_edges(edges,nodes):
    return {(i,j) for i,j in itertools.combinations(range(len(nodes)),2)
            if tuple(sorted((nodes[i],nodes[j]))) in edges}


def verify_local(certificate,global_edges,expected_nodes):
    nodes = certificate['original_vertices']
    assert nodes == expected_nodes == sorted(set(nodes))
    n,edges = graph_edges(certificate['local_graph6'])
    assert n == len(nodes) and edges == induced_edges(global_edges,nodes)
    masks = [m for m in range(1 << n) if stable(m,edges)]
    assert certificate['stable_masks'] == masks
    expected_vertices = {tuple(F((m >> i)&1) for i in range(n)) for m in masks}
    rows = [item['row'] for item in certificate['facets']]
    assert len(rows) == len(set(map(tuple,rows)))
    nonnegative = set()
    upper_covered = set()
    for item,row in zip(certificate['facets'],rows):
        assert len(row) == n+1 and all(isinstance(v,int) for v in row)
        assert all(row[0]+sum(a*b for a,b in zip(row[1:],vertex)) >= 0 for vertex in expected_vertices)
        if item['kind'] == 'nonnegative':
            assert row[0] == 0 and sorted(row[1:]) == [0]*(n-1)+[1]
            nonnegative.add(row[1:].index(1))
            continue
        assert set(row[1:]) <= {-1,0}
        support = [i for i,v in enumerate(row[1:]) if v == -1]
        assert item['support_local_vertices'] == support
        restricted = induced_edges(edges,support)
        alpha = max(m.bit_count() for m in range(1 << len(support)) if stable(m,restricted))
        assert row[0] == alpha
        if item['kind'] == 'clique':
            assert alpha == 1
            upper_covered.update(support)
        else:
            assert item['kind'] == 'SCF_rank'
            check_scf(len(support),restricted)
    # These facts prove that the described H-polytope is bounded.
    assert nonnegative == upper_covered == set(range(n))
    reconstructed = set()
    systems = full_rank = 0
    for active in itertools.combinations(rows,n):
        systems += 1
        vertex = solve_active(active)
        if vertex is None:
            continue
        full_rank += 1
        if all(row[0]+sum(a*b for a,b in zip(row[1:],vertex)) >= 0 for row in rows):
            reconstructed.add(vertex)
    assert reconstructed == expected_vertices
    return {'vertices':n,'stable_polytope_vertices':len(reconstructed),
            'active_systems_checked':systems,'full_rank_systems':full_rank,
            'facet_kinds':sorted(set(r['kind'] for r in certificate['facets']))}


def verify(certificate):
    n,edges = graph_edges(certificate['graph6'])
    assert n == 8
    labels = certificate['pauli_binary_labels']
    words = certificate['pauli_words']
    assert len(labels) == len(words) == n and all(len(word) == 3 and set(word) <= set('IXYZ') for word in words)
    expected_labels = [[sum(int(c in 'XY') << i for i,c in enumerate(word)),
                        sum(int(c in 'YZ') << i for i,c in enumerate(word))] for word in words]
    assert labels == expected_labels
    for i,j in itertools.combinations(range(n),2):
        x,z = labels[i]
        xx,zz = labels[j]
        assert ((((x&zz).bit_count()+(z&xx).bit_count())%2) == 1) == ((i,j) in edges)
    re,im = certificate['integer_state_real'],certificate['integer_state_imag']
    assert len(re) == len(im) == 8 and all(isinstance(v,int) for v in re+im)
    vector = list(zip(re,im))
    norm = sum(a*a+b*b for a,b in vector)
    assert norm == certificate['state_norm_squared'] > 0
    means = [expectation(vector,apply_pauli(label,vector)) for label in labels]
    profile = [v*v for v in means]
    assert means == list(map(F,certificate['expectations']))
    assert profile == list(map(F,certificate['squared_profile']))
    weights = list(map(F,certificate['weights']))
    assert len(weights) == n and all(w >= 0 for w in weights)
    masks = [m for m in range(1 << n) if stable(m,edges)]
    alpha = max(sum(weights[i] for i in range(n) if m >> i & 1) for m in masks)
    value = sum(a*b for a,b in zip(weights,profile))
    assert alpha == F(certificate['exact_stable_bound'])
    assert value == F(certificate['exact_value']) and value-alpha == F(certificate['exact_gap']) > 0
    boundary = certificate['boundary']
    left,right,s = map(set,[boundary['left'],boundary['right'],boundary['separator']])
    assert left|right == set(range(n)) and left&right == s and left-s and right-s
    assert not any(tuple(sorted((i,j))) in edges for i in left-s for j in right-s)
    pair = tuple(boundary['pair'])
    assert [p for p in itertools.combinations(sorted(s),2) if p not in edges] == [pair]
    results = {side:verify_local(certificate['local_certificates'][side],edges,boundary[side]) for side in ('left','right')}
    center,leaves = certificate['non_SCF_claw']['center'],certificate['non_SCF_claw']['leaves']
    assert len(set(leaves)) == 3 and center not in leaves
    assert all(tuple(sorted((center,v))) in edges for v in leaves)
    assert all(tuple(sorted(p)) not in edges for p in itertools.combinations(leaves,2))
    violations = [subset for subset in range(1,1 << n) if sum(profile[i] for i in range(n) if subset >> i & 1) > max((m&subset).bit_count() for m in masks)]
    assert certificate['rank_inequalities_checked'] == 255 and certificate['rank_violations'] == violations == []
    if 'boundary_pair_ranges' in certificate:
        for side in ('left','right'):
            nodes = boundary[side]
            scope = sum(1 << i for i in nodes)
            local_masks = [m for m in masks if m & ~scope == 0]
            target = [F(1)]+[profile[i] for i in nodes]
            ranges = certificate['boundary_pair_ranges'][side]
            for name,sign in [('lower',1),('upper',-1)]:
                dual = list(map(F,ranges[name+'_dual']))
                assert len(dual) == len(target)
                for m in local_masks:
                    column = [1]+[(m >> i)&1 for i in nodes]
                    indicator = int(all(m >> i & 1 for i in pair))
                    assert sum(a*b for a,b in zip(dual,column)) <= sign*indicator
                assert sign*sum(a*b for a,b in zip(dual,target)) == F(ranges[name])
        assert F(certificate['boundary_pair_ranges']['left']['upper']) < F(certificate['boundary_pair_ranges']['right']['lower'])
    assert certificate['generic_quantum_closure_falsified']
    assert not certificate['SCF_conjecture_falsified'] and not certificate['new_imperfect_graph_claim']
    return {'status':'exact_physical_closure_counterexample_verified', 'exact_gap':str(value-alpha),
            'local_all_weight_proofs':results,'quantum_hypothesis_falsified':'generic almost-clique closure only',
            'SCF_conjecture_falsified':False}


def verify_family_sample(certificate,copies):
    """Finite audit of the analytic positive-weight true-twin extension."""
    assert copies >= 2
    ancillas = copies//2
    suffixes = ['Z'*ancillas]
    for q in range(ancillas):
        suffixes.extend('Z'*q+c+'I'*(ancillas-q-1) for c in 'XY')
    suffixes = suffixes[:copies]
    words,weights,old_labels = [],[],[]
    for index,word in enumerate(certificate['pauli_words']):
        for suffix in (suffixes if index == 3 else ['I'*ancillas]):
            words.append(word+suffix)
            weights.append(certificate['weights'][index])
            old_labels.append(index)
    labels = [(sum(int(c in 'XY') << i for i,c in enumerate(word)),
               sum(int(c in 'YZ') << i for i,c in enumerate(word))) for word in words]
    _,base_edges = graph_edges(certificate['graph6'])
    edges = set()
    for i,j in itertools.combinations(range(len(words)),2):
        x,z = labels[i]
        xx,zz = labels[j]
        adjacent = ((x&zz).bit_count()+(z&xx).bit_count())%2 == 1
        expected = old_labels[i] == old_labels[j] or tuple(sorted((old_labels[i],old_labels[j]))) in base_edges
        assert adjacent == expected
        if adjacent:
            edges.add((i,j))
    vector = [(0,0)]*(8*(1 << ancillas))
    for i,(real,imag) in enumerate(zip(certificate['integer_state_real'],certificate['integer_state_imag'])):
        vector[i << ancillas] = (real,imag)
    means = [expectation(vector,apply_pauli(label,vector)) for label in labels]
    value = sum(F(w)*v*v for w,v in zip(weights,means))
    n = len(words)
    alpha = max(sum(weights[i] for i in range(n) if mask >> i & 1) for mask in range(1 << n) if stable(mask,edges))
    assert all(w > 0 for w in weights) and alpha == certificate['exact_stable_bound']
    assert value == F(certificate['exact_value']) and value-alpha == F(certificate['exact_gap'])
    return {'vertices':n,'copies':copies,'qubits':3+ancillas,'exact_gap':str(value-alpha)}


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Assertions required.')
    print(json.dumps(verify(json.loads((DATA/'almost_clique_closure_counterexample.json').read_text()))))
