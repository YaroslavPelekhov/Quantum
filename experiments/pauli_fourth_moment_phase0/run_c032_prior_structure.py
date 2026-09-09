"""Small exact structural audit of direct known graph-closure routes."""
import itertools
import json
from c020_exact_certificate import DATA
from verify_scf_generalization import graph_edges
from verify_scf_two_xx_weight import verify as verify_source
from verify_c031_exact_six import check


def connected(neighbors):
    reached={0};todo=[0]
    while todo:
        new=neighbors[todo.pop()]-reached;reached|=new;todo.extend(new)
    return len(reached)==len(neighbors)


def audit(neighbors):
    n=len(neighbors);vertices=set(range(n));traces=[]
    twins=[(i,j) for i,j in itertools.combinations(range(n),2) if neighbors[i]-{j}==neighbors[j]-{i}]
    for i,j in itertools.combinations(range(n),2):
        current={i,j};trace=[i,j]
        while True:
            forced=next((v for v in sorted(vertices-current) if 0<len(neighbors[v]&current)<len(current)),None)
            if forced is None:break
            current.add(forced);trace.append(forced)
        traces.append(trace)
    return dict(connected=connected(neighbors),complement_connected=connected([vertices-{i}-g for i,g in enumerate(neighbors)]),
                twins=twins,pair_closure_traces=traces,modular_prime=all(len(t)==n for t in traces))


def verify_traces(neighbors,result):
    n=len(neighbors);traces=result['pair_closure_traces']
    assert [t[:2] for t in traces]==[list(p) for p in itertools.combinations(range(n),2)]
    for trace in traces:
        current=set(trace[:2])
        for v in trace[2:]:
            assert v not in current and 0<=v<n
            statuses={u in neighbors[v] for u in current}
            assert statuses=={False,True}
            current.add(v)
        assert all(len(neighbors[v]&current) in (0,len(current)) for v in set(range(n))-current)
    assert result['modular_prime']==all(len(set(t))==n for t in traces)


if __name__=='__main__':
    source=json.loads((DATA/'scf_two_xx_weight_c014.json').read_text());verify_source(source)
    check(json.loads((DATA/'c031_exact_six_certificate.json').read_text()))
    n,edges=graph_edges(source['graph6'])
    neighbors=[{j for j in range(n) if tuple(sorted((i,j))) in edges} for i in range(n)]
    result=audit(neighbors);verify_traces(neighbors,result)
    row=source['records'][0]
    assert row['facet_inducing'] and all(w>0 for w in row['weights']) and len(set(row['weights']))>1
    result.update(non_h_perfect_from_nonuniform_facet=True,priority_confirmed=False,all_weights_proved=False)
    with (DATA/'c032_prior_structure.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='pair_closure_traces'},indent=2))
