"""Independent exact checker for generalization obstructions (stdlib only).

No numerical solver, NumPy, graph library, or symbolic algebra is imported.
Pauli actions on Gaussian-integer state vectors are computed bit by bit.
"""
from fractions import Fraction as F
import itertools
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def graph_edges(code):
    values = [ord(ch)-63 for ch in code]
    n = values[0]
    assert 1 <= n <= 62
    bits = [(v >> k) & 1 for v in values[1:] for k in range(5,-1,-1)]
    pairs = [(i,j) for j in range(1,n) for i in range(j)]
    assert len(bits) >= len(pairs)
    return n, {p for p,b in zip(pairs,bits) if b}


def stable(mask, edges):
    return all(not (mask >> i & 1 and mask >> j & 1) for i,j in edges)


def check_scf(n, edges):
    def clique(nodes):
        return all(tuple(sorted(p)) in edges for p in itertools.combinations(nodes,2))
    neighbors = [{j for j in range(n) if tuple(sorted((i,j))) in edges} for i in range(n)]
    reached = {0}
    while True:
        expanded = reached | set().union(*(neighbors[i] for i in reached))
        if expanded == reached:
            break
        reached = expanded
    assert len(reached) == n  # Every stored obstruction is connected.
    assert all(any(tuple(sorted(p)) in edges for p in itertools.combinations(leaves,2))
               for node in range(n) for leaves in itertools.combinations(neighbors[node],3))
    for mask in range(1,1 << n):
        nodes = {i for i in range(n) if mask >> i & 1}
        if clique(nodes) and all(clique(neighbors[i]-nodes) for i in nodes):
            return True
    raise AssertionError('no simplicial clique')


def verify_gluing(record):
    n, edges = graph_edges(record['graph6'])
    check_scf(n,edges)
    masks = [m for m in range(1 << n) if stable(m,edges)]
    x = list(map(F,record['profile']))
    w = list(map(F,record['weights']))
    assert len(x) == len(w) == n and all(v >= 0 for v in x)
    assert all(v >= 0 for v in w)
    for subset in range(1,1 << n):
        assert sum(x[i] for i in range(n) if subset >> i & 1) <= max((m&subset).bit_count() for m in masks)
    left,right,separator = map(set,[record['left_vertices'],record['right_vertices'],record['separator']])
    assert left|right == set(range(n)) and left&right == separator
    assert not any(tuple(sorted((i,j))) in edges for i in left-separator for j in right-separator)
    cover = record['separator_clique_cover']
    assert 1 <= len(cover) <= 2 and left-separator and right-separator
    assert set().union(*map(set,cover)) == separator
    assert all(all(tuple(sorted(p)) in edges for p in itertools.combinations(part,2)) for part in cover)
    for nodes, name in [(left,'left_STAB_decomposition'),(right,'right_STAB_decomposition')]:
        terms = record[name]
        assert sum(F(t['probability']) for t in terms) == 1
        reconstructed = [F(0)]*n
        for term in terms:
            chosen = set(term['stable_set'])
            probability = F(term['probability'])
            assert probability >= 0 and chosen <= nodes
            assert stable(sum(1 << i for i in chosen),edges)
            for i in chosen:
                reconstructed[i] += probability
        assert all(reconstructed[i] == x[i] for i in nodes)
    alpha = max(sum(w[i] for i in range(n) if m >> i & 1) for m in masks)
    value = sum(a*b for a,b in zip(w,x))
    assert alpha == F(record['exact_stable_bound'])
    assert value == F(record['exact_profile_value']) and value-alpha == F(record['exact_violation']) > 0
    for pair_range in record['separator_pair_ranges']:
        pair = pair_range['pair']
        assert len(pair) == 2 and pair[0] < pair[1]
        assert set(pair) <= separator and tuple(pair) not in edges
        for side,nodes in [('left',sorted(left)),('right',sorted(right))]:
            local_masks = [m for m in range(1 << n) if stable(m,edges) and all(not (m >> i & 1) for i in set(range(n))-set(nodes))]
            target = [F(1)]+[x[i] for i in nodes]
            for name,sign in [('lower',1),('upper',-1)]:
                dual = list(map(F,pair_range[side][name+'_dual']))
                assert len(dual) == len(target)
                for m in local_masks:
                    column = [1]+[(m >> i)&1 for i in nodes]
                    indicator = int(all(m >> i & 1 for i in pair))
                    assert sum(a*v for a,v in zip(dual,column)) <= sign*indicator
                assert sign*sum(a*v for a,v in zip(dual,target)) == F(pair_range[side][name])
    return value-alpha


def apply_pauli(label, vector):
    dimension = len(vector)
    qubits = dimension.bit_length()-1
    assert 1 << qubits == dimension
    x,z = label
    assert 0 <= x < dimension and 0 <= z < dimension
    output = [(0,0)]*dimension
    for column,(real,imag) in enumerate(vector):
        toggle = sum(((x >> bit)&1) << (qubits-1-bit) for bit in range(qubits))
        phase = ((x&z).bit_count()+2*sum(((z >> bit)&1)*((column >> (qubits-1-bit))&1) for bit in range(qubits)))%4
        for _ in range(phase):
            real,imag = -imag,real
        output[column^toggle] = (real,imag)
    return output


def expectation(vector, transformed):
    real = sum(a*c+b*d for (a,b),(c,d) in zip(vector,transformed))
    imag = sum(a*d-b*c for (a,b),(c,d) in zip(vector,transformed))
    assert imag == 0
    norm = sum(a*a+b*b for a,b in vector)
    assert norm > 0
    return F(real,norm)


def exact_pair_profile(record, pairs):
    n,edges = graph_edges(record['graph6'])
    check_scf(n,edges)
    labels = record['pauli_binary_labels']
    assert len(record['integer_state_real']) == len(record['integer_state_imag'])
    vector = list(zip(record['integer_state_real'],record['integer_state_imag']))
    assert len(labels) == n
    assert all(isinstance(x,int) for pair in vector for x in pair)
    assert len(pairs) == len(set(pairs))
    assert all(0 <= i < j < n and (i,j) not in edges for i,j in pairs)
    if 'state_norm_squared' in record:
        assert sum(a*a+b*b for a,b in vector) == record['state_norm_squared']
    for i,j in itertools.combinations(range(n),2):
        x,z = labels[i]
        xx,zz = labels[j]
        assert (((x&zz).bit_count()+(z&xx).bit_count())%2 == 1) == ((i,j) in edges)
    r = [expectation(vector,apply_pauli(label,vector)) for label in labels]
    q = [expectation(vector,apply_pauli(labels[i],apply_pauli(labels[j],vector))) for i,j in pairs]
    x = [v*v for v in r]
    y = [max(F(0),(x[i]+x[j]+v*v-1)/2) for (i,j),v in zip(pairs,q)]
    assert x+y == list(map(F,record['proposed_lift']))
    return n,edges,x+y,r,q


def verify_pair_failure(record):
    pairs = [tuple(p) for p in record['pairs']]
    n,edges,point,r,q = exact_pair_profile(record,pairs)
    assert r == list(map(F,record['expectations'])) and q == list(map(F,record['pair_product_expectations']))
    witness = record['separator']
    a = list(map(F,witness['coefficients']))
    assert len(a) == len(point) == n+len(pairs)
    vertices = [[(m >> i)&1 for i in range(n)]+[int(bool(m >> i & 1 and m >> j & 1)) for i,j in pairs]
                for m in range(1 << n) if stable(m,edges)]
    bound = max(sum(c*v for c,v in zip(a,vertex)) for vertex in vertices)
    value = sum(c*v for c,v in zip(a,point))
    assert bound == F(witness['exact_vertex_bound']) and value == F(witness['exact_proposed_lift_value'])
    assert value-bound == F(witness['exact_gap']) > 0
    return value-bound


def verify_all():
    if not __debug__:
        raise RuntimeError('Do not disable assertions for exact verification.')
    gluing = json.loads((DATA/'scf_gluing_obstruction.json').read_text())
    gaps = [verify_gluing(row) for row in gluing['records']]
    expected = {5,7,9,15,23,24,25,26,27,33,34,44,48}
    assert len(gaps) == 13 and {r['representative_index'] for r in gluing['records']} == expected
    pair = json.loads((DATA/'scf_pair_completion_audit.json').read_text())
    by_label = {'residual_'+str(r['representative_index'])+'_separator': r for r in gluing['records']}
    assert len(pair['records']) == 13 and {r['label'] for r in pair['records']} == set(by_label)
    for row in pair['records']:
        if 'separator' not in row:
            continue  # No proof claim is made for searches without a witness.
        original = by_label[row['label']]
        assert row['graph6'] == original['graph6']
        _,edges = graph_edges(row['graph6'])
        expected_pairs = [p for p in itertools.combinations(sorted(original['separator']),2) if p not in edges]
        assert [tuple(p) for p in row['pairs']] == expected_pairs
    failures = [verify_pair_failure(row) for row in pair['records'] if 'separator' in row]
    assert len(failures) == 5
    control = pair['exact_G15_control']
    n,edges = graph_edges(control['graph6'])
    pairs = [p for p in itertools.combinations(range(n),2) if p not in edges]
    _,_,point,_,_ = exact_pair_profile(control,pairs)
    assert 2*sum(point[:n])-sum(point[n:]) == F(179,50)
    assert max(m.bit_count() for m in range(1 << n) if stable(m,edges)) == 3
    result = {'exact_gluing_obstructions': len(gaps), 'exact_quantum_pair_recipe_counterexamples': len(failures),
              'G15_exact_gap': '29/50', 'arithmetic': 'integers and Fraction; no solver',
              'main_weighted_SCF_conjecture_falsified': False, 'status': 'all_independent_exact_checks_passed'}
    return result


if __name__ == '__main__':
    print(json.dumps(verify_all()))
