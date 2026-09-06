"""C003: exact physical witness against generic almost-clique closure.

The graph is the published G8, not a newly discovered imperfect graph.
Numerical search only proposes a small integer state; acceptance is exact.
"""
from fractions import Fraction as F
import itertools
import json
from pathlib import Path
import cdd.gmp as cdd
import networkx as nx
import numpy as np
from run_almost_clique_closure_audit import DATA, fetch
from run_published_g9_control import pauli_word
from run_scf_exact_facet_census import primitive, stable_masks
from run_scf_gluing_obstruction import pair_range
from verify_scf_generalization import apply_pauli, expectation, check_scf


def binary_labels(words):
    return [[sum((ch in 'XY') << i for i,ch in enumerate(word)),
             sum((ch in 'YZ') << i for i,ch in enumerate(word))] for word in words]


def rational_profile(labels, real,imag):
    vector = list(zip(map(int,real),map(int,imag)))
    r = [expectation(vector,apply_pauli(label,vector)) for label in labels]
    return r,[v*v for v in r]


def local_certificate(graph,nodes):
    local = nx.convert_node_labels_to_integers(graph.subgraph(nodes),ordering='sorted')
    n = len(local)
    masks = stable_masks(local)
    points = [[1]+[(m >> i)&1 for i in range(n)] for m in masks]
    hull = cdd.polyhedron_from_matrix(cdd.matrix_from_array(points,rep_type=cdd.RepType.GENERATOR))
    rows = sorted(set(primitive(row) for row in cdd.copy_inequalities(hull).array))
    certificates = []
    for row in rows:
        if row[0] == 0:
            assert sorted(row[1:]) == [0]*(n-1)+[1]
            certificates.append({'kind':'nonnegative','row':row})
            continue
        assert set(row[1:]) <= {-1,0}
        support = [i for i,w in enumerate(row[1:]) if w == -1]
        induced = nx.convert_node_labels_to_integers(local.subgraph(support),ordering='sorted')
        alpha = max(m.bit_count() for m in stable_masks(induced))
        assert row[0] == alpha
        if alpha == 1:
            kind = 'clique'
        else:
            check_scf(len(induced),set(tuple(sorted(e)) for e in induced.edges()))
            kind = 'SCF_rank'
        certificates.append({'kind':kind,'support_local_vertices':support,'row':row})
    return {'original_vertices':nodes,'local_graph6':nx.to_graph6_bytes(local,header=False).decode().strip(),
            'facets':certificates,'stable_masks':masks,
            'scope':'all weights and states; facet completeness needs independent verification'}


def main():
    entry = fetch(8)[0]
    assert entry[0] == 'GCrdrk'
    words = [''.join('IXYZ'[i] for i in row) for row in entry[2]]
    operators = np.asarray([pauli_word(word) for word in words])
    labels = binary_labels(words)
    graph = nx.from_graph6_bytes(entry[0].encode())
    for i,j in itertools.combinations(range(8),2):
        assert (np.linalg.norm(operators[i]@operators[j]+operators[j]@operators[i]) < 1e-8) == graph.has_edge(i,j)
    weights = np.asarray([1,1,1,1,1,1,2,2],float)
    alpha = max(sum(int(weights[i]) for i in range(8) if m >> i & 1) for m in stable_masks(graph))
    assert alpha == 3
    best_value = -1
    best_state = None
    starts_tested = 0
    for tail in itertools.product((-1.,1.),repeat=7):
        coefficients = np.sqrt(weights)*np.asarray((1.,)+tail)
        coefficients /= np.linalg.norm(coefficients)
        for _ in range(512):
            h = np.einsum('i,ijk->jk',coefficients*np.sqrt(weights),operators)
            eigenvalues,eigenvectors = np.linalg.eigh(h)
            state = eigenvectors[:,np.argmax(np.abs(eigenvalues))]
            means = np.einsum('j,ijk,k->i',state.conj(),operators,state).real
            update = np.sqrt(weights)*means
            update /= np.linalg.norm(update)
            delta = min(np.linalg.norm(update-coefficients),np.linalg.norm(update+coefficients))
            coefficients = update
            if delta < 1e-13:
                break
        value = float(weights@(means*means))
        starts_tested += 1
        if value > best_value:
            best_value,best_state = value,state.copy()
    assert best_value > 3+1e-7, best_value
    largest = np.argmax(np.abs(best_state))
    state = best_state*np.exp(-1j*np.angle(best_state[largest]))
    state /= np.max(np.abs(state))
    exact = None
    for scale in (1,2,3,4,5,8,10,16,32,64,128,1000,10000):
        real,imag = np.rint(scale*state.real).astype(int),np.rint(scale*state.imag).astype(int)
        means,profile = rational_profile(labels,real,imag)
        value = sum(F(int(w))*v for w,v in zip(weights,profile))
        if value > alpha:
            exact = {'integer_state_real':real.tolist(),'integer_state_imag':imag.tolist(),
                     'state_norm_squared':sum(int(a)**2+int(b)**2 for a,b in zip(real,imag)),
                     'expectations':list(map(str,means)),'squared_profile':list(map(str,profile)),
                     'rounding_scale':scale,'exact_value':str(value),'exact_gap':str(value-alpha)}
            break
    assert exact is not None
    boundary = json.loads((DATA/'almost_clique_closure_audit.json').read_text())['records'][0]['decompositions'][0]
    result = {'experiment':'C003_exact_generic_almost_clique_closure_counterexample',
              'date':'2026-09-06','extraction_preregistration_commit':'b281e62',
              'graph6':entry[0],'published_graph':'G8 of Xu et al.; benchmark test8.txt row 1',
              'pauli_words':words,'pauli_binary_labels':labels,'weights':list(map(int,weights)),
              'exact_stable_bound':alpha,'numerical_search_lower_bound':best_value,
              'sign_starts_tested':starts_tested,'boundary':boundary,
              'local_certificates':{side:local_certificate(graph,boundary[side]) for side in ('left','right')},
              'generic_quantum_closure_falsified':True,'SCF_conjecture_falsified':False,
              'new_imperfect_graph_claim':False,**exact}
    claws = [(center,list(leaves)) for center in graph for leaves in itertools.combinations(graph.neighbors(center),3)
             if graph.subgraph(leaves).number_of_edges() == 0]
    assert claws
    result['non_SCF_claw'] = {'center':claws[0][0],'leaves':claws[0][1]}
    masks = stable_masks(graph)
    profile = list(map(F,result['squared_profile']))
    rank_violations = [subset for subset in range(1,256) if sum(profile[i] for i in range(8) if subset >> i & 1) > max((m&subset).bit_count() for m in masks)]
    result['rank_inequalities_checked'] = 255
    result['rank_violations'] = rank_violations
    result['boundary_pair_ranges'] = {side:pair_range(graph,boundary[side],profile,boundary['pair']) for side in ('left','right')}
    (DATA/'almost_clique_closure_counterexample.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('local_certificates',)}),flush=True)


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Assertions required.')
    main()
