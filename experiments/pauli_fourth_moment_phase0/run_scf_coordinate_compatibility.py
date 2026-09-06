"""C002: try to falsify coordinatewise (not simultaneous) boundary gluing."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from verify_scf_generalization import graph_edges, stable
from verify_scf_coordinate_compatibility import verify_witness

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def joint_sum_ranges(row):
    n,edges = graph_edges(row['graph6'])
    x = list(map(F,row['profile']))
    pairs = row['boundary']['pairs']
    output = {}
    for side in ('left','right'):
        nodes = row['boundary'][side]
        scope = sum(1 << i for i in nodes)
        masks = [m for m in range(1 << n) if m & ~scope == 0 and stable(m,edges)]
        columns = [[1]+[(m >> i)&1 for i in nodes] for m in masks]
        objective = [sum(int(all(m >> i & 1 for i in p)) for p in pairs) for m in masks]
        target = [F(1)]+[x[i] for i in nodes]
        ranges = {}
        for sign,name in ((1,'lower'),(-1,'upper')):
            result = linprog(np.array(objective)*sign,A_eq=np.array(columns).T,
                             b_eq=np.array(target,float),bounds=(0,None),method='highs')
            assert result.success
            dual = [F(float(v)).limit_denominator(1_000_000) for v in result.eqlin.marginals]
            assert all(sum(a*b for a,b in zip(dual,c)) <= sign*v for c,v in zip(columns,objective))
            bound = sign*sum(a*b for a,b in zip(dual,target))
            ranges[name] = str(bound)
            ranges[name+'_dual'] = list(map(str,dual))
        output[side] = ranges
    return output


def weights_by_label():
    source = json.loads((DATA/'scf_order9_facet_reduction.json').read_text())
    result = {f"order9_residual_{r['representative_index']}":list(map(lambda x:F(str(x)),r['weights'])) for r in source['residual_atoms']}
    frontier = json.loads((DATA/'scf_order10_frontier.json').read_text())
    result.update({f'order10_frontier_{i}':list(map(F,r['integer_weights'])) for i,r in enumerate(frontier['representatives'])})
    return result


def attack(record, weights):
    n,edges = graph_edges(record['graph6'])
    all_masks = [m for m in range(1 << n) if stable(m,edges)]
    witness = record['best']
    pairs = witness['pairs']
    blocks = []
    dimension = n
    for pair in pairs:
        sides = []
        for side in ('left','right'):
            nodes = witness[side]
            scope = sum(1 << i for i in nodes)
            masks = [m for m in all_masks if m & ~scope == 0]
            sides.append((nodes,masks,dimension))
            dimension += len(masks)
        blocks.append((pair,sides))
    equalities = []
    targets = []
    for pair,sides in blocks:
        for nodes,masks,offset in sides:
            row = np.zeros(dimension)
            row[offset:offset+len(masks)] = 1
            equalities.append(row)
            targets.append(1)
            for i in nodes:
                row = np.zeros(dimension)
                row[i] = -1
                row[offset:offset+len(masks)] = [(m >> i)&1 for m in masks]
                equalities.append(row)
                targets.append(0)
        row = np.zeros(dimension)
        for sign,(_,masks,offset) in zip((1,-1),sides):
            row[offset:offset+len(masks)] = [sign*int(all(m >> i & 1 for i in pair)) for m in masks]
        equalities.append(row)
        targets.append(0)
    ranks = np.zeros(((1 << n)-1,dimension))
    bounds = []
    for subset in range(1,1 << n):
        ranks[subset-1,:n] = [(subset >> i)&1 for i in range(n)]
        bounds.append(max((m&subset).bit_count() for m in all_masks))
    objective = np.zeros(dimension)
    objective[:n] = [-float(w) for w in weights]
    result = linprog(objective,A_ub=ranks,b_ub=bounds,A_eq=equalities,b_eq=targets,
                     bounds=(0,None),method='highs')
    assert result.success, result.message
    alpha = max(sum(weights[i] for i in range(n) if m >> i & 1) for m in all_masks)
    row = {'label':record['label'], 'graph6':record['graph6'], 'boundary':witness,
           'weights':list(map(str,weights)), 'stable_bound':str(alpha),
           'numerical_lp_value':float(-result.fun), 'numerical_gap':float(-result.fun-float(alpha))}
    if -result.fun <= float(alpha)+1e-8:
        return {**row,'status':'no_violation_for_this_objective_not_an_exact_upper_certificate'}
    rational = [F(float(x)).limit_denominator(1_000_000) for x in result.x]
    row['profile'] = list(map(str,rational[:n]))
    row['pairwise_decompositions'] = []
    for pair,sides in blocks:
        local = {'pair':pair}
        for name,(nodes,masks,offset) in zip(('left','right'),sides):
            local[name] = [{'stable_set':[i for i in range(n) if m >> i & 1],
                            'probability':str(rational[offset+k])}
                           for k,m in enumerate(masks) if rational[offset+k]]
        row['pairwise_decompositions'].append(local)
    value = sum(w*x for w,x in zip(weights,rational[:n]))
    row.update({'exact_profile_value':str(value),'exact_gap':str(value-alpha),
                'status':'exact_coordinatewise_gluing_obstruction',
                'is_physical_quantum_counterexample':False})
    if row['label'] == 'order9_residual_33':
        row['joint_pair_sum_ranges'] = joint_sum_ranges(row)
    verify_witness(row)
    return row


def main():
    coverage_path = DATA/'scf_separator_coverage.json'
    source = json.loads(coverage_path.read_text())
    selected = [r for r in source['records'] if r['minimum_pair_events'] > 1]
    controls = [r for r in source['records'] if r['minimum_pair_events'] == 1][:3]
    weights = weights_by_label()
    records = []
    for entry in selected+controls:
        row = attack(entry,weights[entry['label']])
        row['role'] = 'attack' if entry in selected else 'single_pair_control'
        records.append(row)
        print(json.dumps({k:row[k] for k in ('label','status','numerical_gap')}),flush=True)
    result = {'experiment':'C002_coordinatewise_boundary_compatibility',
              'date':'2026-09-06', 'preregistration_commit':'b70d719',
              'coverage_source_sha256':hashlib.sha256(coverage_path.read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
              'attacks':len(selected),'controls':len(controls),
              'exact_obstructions':sum('profile' in r for r in records),
              'quantum_conjecture_falsified':False,
              'records':records}
    (DATA/'scf_coordinate_compatibility.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'records'}),flush=True)


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Assertions required.')
    main()
