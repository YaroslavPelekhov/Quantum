"""Independent C004 acceptance: graph6, four-subsets, exact binary parity."""
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
from verify_scf_generalization import graph_edges, stable, check_scf, apply_pauli, expectation
from fractions import Fraction

DATA=Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def explicit_claws(nodes,edges):
    result=[]
    for four in itertools.combinations(sorted(nodes),4):
        induced=[(i,j) for i,j in itertools.combinations(four,2) if (i,j) in edges]
        if len(induced)!=3: continue
        degrees=Counter(x for edge in induced for x in edge)
        centers=[i for i in four if degrees[i]==3]
        if len(centers)==1 and sorted(degrees.values())==[1,1,1,3]:
            c=centers[0]
            result.append([c,*[i for i in four if i!=c]])
    return sorted(result)


def verify_record(row):
    n,edges=graph_edges(row['graph6'])
    b=row['boundary']
    s,l,r=map(set,(b['separator'],b['left'],b['right']))
    assert l|r==set(range(n)) and l&r==s and l-s and r-s
    assert not any(tuple(sorted((x,y))) in edges for x in l-s for y in r-s)
    assert [list(e) for e in itertools.combinations(sorted(s),2) if e not in edges]==[b['pair']]
    u,v=b['pair']
    for side,nodes in [('left',l),('right',r)]:
        expected=[]
        for z in sorted(nodes-s):
            uv=[int(tuple(sorted((z,t))) in edges) for t in (u,v)]
            expected.append({'vertex':z,'uv_neighbors':uv,'J_odd':bool(sum(uv)%2)})
        assert expected==row['parity'][side]
        assert row['J_central'][side]==(not any(item['J_odd'] for item in expected))
        assert row['local_claws'][side]==explicit_claws(nodes,edges)
    all_claws=explicit_claws(range(n),edges)
    spanning=[c for c in all_claws if set(c[1:])&(l-s) and set(c[1:])&(r-s)]
    assert row['cross_claws']==spanning
    assert row['global_claw_free']==(not all_claws)
    # Independent finite audit of the connected false-twin proposition.
    if row['global_claw_free'] and all(row['J_central'].values()):
        reached={0}
        while True:
            more=reached|{j for i in reached for j in range(n) if tuple(sorted((i,j))) in edges}
            if more==reached: break
            reached=more
        if len(reached)==n:
            assert max(mask.bit_count() for mask in range(1<<n) if stable(mask,edges))==2


def verify_exhaustive(saved):
    fixed=[(0,2),(1,2)]
    free=[(x,y) for x in range(3) for y in range(3,7)]+[(3,4),(5,6)]
    assert list(map(tuple,saved['fixed_edges']))==fixed
    assert list(map(tuple,saved['free_edges']))==free
    counts=Counter()
    bitstream=bytearray()
    for mask in range(1<<14):
        edges=set(fixed)|{e for i,e in enumerate(free) if mask>>i&1}
        all_claws=explicit_claws(range(7),edges)
        local_claws=[c for c in all_claws if set(c)<=set([0,1,2,3,4]) or set(c)<=set([0,1,2,5,6])]
        counts['graphs']+=1
        counts['locally_claw_free']+=not local_claws
        counts['predicted_globally_claw_free']+=not all_claws
        counts['local_pass_cross_fail']+=not local_claws and bool(all_claws)
        bitstream.append(int(not all_claws))
    assert dict(counts)==saved['counts']
    assert hashlib.sha256(bitstream).hexdigest()==saved['acceptance_bitstream_sha256']
    return dict(counts)


def verify_dephasing(c):
    words=c['pauli_words']
    assert words==['XI','ZX','IZ','IX','YZ'] and c['pair']==[0,2] and c['J_word']=='XZ'
    labels=[(sum(int(ch in 'XY')<<i for i,ch in enumerate(w)),
             sum(int(ch in 'YZ')<<i for i,ch in enumerate(w))) for w in words]
    edges={(i,j) for i,j in itertools.combinations(range(5),2)
           if ((labels[i][0]&labels[j][1]).bit_count()+(labels[i][1]&labels[j][0]).bit_count())%2}
    assert edges=={(0,1),(1,2),(2,3),(3,4),(0,4)}
    weights=c['weights']
    assert weights==[1,1,1,3,1]
    alpha=max(sum(weights[i] for i in range(5) if m>>i&1) for m in range(32) if stable(m,edges))
    assert alpha==c['exact_stable_bound']==4
    for name,value in [('coherent',4),('sector',2)]:
        vector=[(v,0) for v in c[name+'_integer_state']]
        assert len(vector)==4
        means=[expectation(vector,apply_pauli(p,vector)) for p in labels]
        assert means==list(map(Fraction,c[name+'_expectations']))
        assert sum(w*r*r for w,r in zip(weights,means))==value
        if name=='sector': assert expectation(vector,apply_pauli((1,2),vector))==1
    odd=[i for i,p in enumerate(labels) if ((p[0]&2).bit_count()+(p[1]&1).bit_count())%2]
    assert odd==[3,4]
    # For J-invariant states, the odd expectations vanish. The remaining
    # path P3 has value <=2 by its two edge/clique uncertainty bounds.
    assert edges&{(0,1),(0,2),(1,2)}=={(0,1),(1,2)}
    assert c['exact_sector_optimum']==2 and c['exact_coherent_value']==4


def verify(report,exhaustive=True):
    raw=(DATA/'scf_separator_coverage.json').read_bytes().replace(b'\r\n',b'\n')
    assert hashlib.sha256(raw).hexdigest()==report['source_sha256']
    source=[r for r in json.loads(raw)['records'] if r['minimum_pair_events']==1]
    assert len(report['records'])==report['weighted_rows']==len(source)==36
    assert len({r['graph6'] for r in report['records']})==report['distinct_graphs']==35
    for row,old in zip(report['records'],source):
        assert (row['label'],row['graph6'])==(old['label'],old['graph6'])
        assert row['boundary']=={**{k:old['best'][k] for k in ('separator','left','right')},'pair':old['best']['pairs'][0]}
        verify_record(row)
        n,edges=graph_edges(row['graph6'])
        check_scf(n,edges)
        assert row['global_claw_free']
    assert len(report['controls'])==3
    for row in report['controls']: verify_record(row)
    assert [r['label'] for r in report['controls']]==['C4','C5','published_G8']
    assert [sum(r['J_central'].values()) for r in report['controls']]==[2,1,1]
    assert [r['global_claw_free'] for r in report['controls']]==[True,True,False]
    histogram=dict(Counter(str(sum(r['J_central'].values())) for r in report['records']))
    assert histogram==report['central_side_histogram']=={'1':36}
    assert not report['quantum_compatibility_proved'] and not report['SCF_conjecture_falsified']
    verify_dephasing(report['dephasing_control'])
    counts=verify_exhaustive(report['exhaustive_template']) if exhaustive else None
    return {'status':'independent_C004_gate_verified','one_sided_central_rows':36,
            'exhaustive_counts':counts,'quantum_compatibility_proved':False}


if __name__=='__main__':
    if not __debug__: raise RuntimeError('Assertions required.')
    print(json.dumps(verify(json.loads((DATA/'scf_cross_claw_gate.json').read_text()))))
