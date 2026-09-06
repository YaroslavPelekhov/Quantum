"""Verify rational C002 obstructions without any numerical/graph library."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
from verify_scf_generalization import graph_edges, stable, check_scf

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def verify_witness(row):
    n,edges = graph_edges(row['graph6'])
    check_scf(n,edges)
    x,w = map(lambda values:list(map(F,values)),[row['profile'],row['weights']])
    assert len(x) == len(w) == n and all(v >= 0 for v in x+w)
    masks = [m for m in range(1 << n) if stable(m,edges)]
    for subset in range(1,1 << n):
        assert sum(x[i] for i in range(n) if subset >> i & 1) <= max((m&subset).bit_count() for m in masks)
    boundary = row['boundary']
    left,right,s = map(set,[boundary['left'],boundary['right'],boundary['separator']])
    assert left|right == set(range(n)) and left&right == s and left-s and right-s
    assert not any(tuple(sorted((i,j))) in edges for i in left-s for j in right-s)
    cover = boundary['clique_cover']
    assert len(cover) <= 2 and set().union(*map(set,cover)) == s
    assert all(all((i,j) in edges for i in part for j in part if i < j) for part in cover)
    pairs = [(i,j) for i in sorted(s) for j in sorted(s) if i < j and (i,j) not in edges]
    assert [tuple(p) for p in boundary['pairs']] == pairs
    assert [tuple(r['pair']) for r in row['pairwise_decompositions']] == pairs
    for record in row['pairwise_decompositions']:
        shared = []
        for side,nodes in [('left',left),('right',right)]:
            terms = record[side]
            assert sum(F(t['probability']) for t in terms) == 1
            marginal = [F(0)]*n
            paired = F(0)
            for term in terms:
                probability = F(term['probability'])
                chosen = set(term['stable_set'])
                assert probability >= 0 and chosen <= nodes
                assert stable(sum(1 << i for i in chosen),edges)
                for i in chosen:
                    marginal[i] += probability
                if set(record['pair']) <= chosen:
                    paired += probability
            assert all(marginal[i] == x[i] for i in nodes)
            shared.append(paired)
        assert shared[0] == shared[1]
    alpha = max(sum(w[i] for i in range(n) if m >> i & 1) for m in masks)
    value = sum(a*b for a,b in zip(w,x))
    assert alpha == F(row['stable_bound']) and value == F(row['exact_profile_value'])
    assert value-alpha == F(row['exact_gap']) > 0
    assert not row['is_physical_quantum_counterexample']
    if 'joint_pair_sum_ranges' in row:
        for side,nodes in [('left',sorted(left)),('right',sorted(right))]:
            scope = sum(1 << i for i in nodes)
            local = [m for m in masks if m & ~scope == 0]
            target = [F(1)]+[x[i] for i in nodes]
            ranges = row['joint_pair_sum_ranges'][side]
            for name,sign in [('lower',1),('upper',-1)]:
                dual = list(map(F,ranges[name+'_dual']))
                assert len(dual) == len(target)
                for m in local:
                    column = [1]+[(m >> i)&1 for i in nodes]
                    event_sum = sum(int(all(m >> i & 1 for i in pair)) for pair in pairs)
                    assert sum(a*b for a,b in zip(dual,column)) <= sign*event_sum
                assert sign*sum(a*b for a,b in zip(dual,target)) == F(ranges[name])
        assert F(row['joint_pair_sum_ranges']['left']['upper']) < F(row['joint_pair_sum_ranges']['right']['lower'])
    return value-alpha


def verify_all():
    data = json.loads((DATA/'scf_coordinate_compatibility.json').read_text())
    raw = (DATA/'scf_separator_coverage.json').read_bytes().replace(b'\r\n',b'\n')
    assert hashlib.sha256(raw).hexdigest() == data['coverage_source_sha256']
    corpus = json.loads(raw)['records']
    selected = [r for r in corpus if r['minimum_pair_events'] > 1]
    controls = [r for r in corpus if r['minimum_pair_events'] == 1][:3]
    assert [r['label'] for r in data['records']] == [r['label'] for r in selected+controls]
    assert (data['attacks'],data['controls']) == (11,3)
    original = {r['label']:r for r in corpus}
    residual = json.loads((DATA/'scf_order9_facet_reduction.json').read_text())['residual_atoms']
    frontier = json.loads((DATA/'scf_order10_frontier.json').read_text())['representatives']
    weights = {f"order9_residual_{r['representative_index']}":[F(str(w)) for w in r['weights']] for r in residual}
    weights.update({f'order10_frontier_{i}':list(map(F,r['integer_weights'])) for i,r in enumerate(frontier)})
    gaps = []
    for row in data['records']:
        source = original[row['label']]
        assert row['graph6'] == source['graph6'] and row['boundary'] == source['best']
        assert list(map(F,row['weights'])) == weights[row['label']]
        if 'profile' in row:
            gaps.append(verify_witness(row))
    assert len(gaps) == data['exact_obstructions'] and not data['quantum_conjecture_falsified']
    return {'attacks':11,'controls':3,'exact_obstructions':len(gaps),
            'status':'independent_rational_witness_checks_passed',
            'numerical_nonviolations_are_not_proofs':True}


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Assertions required.')
    print(json.dumps(verify_all()))
