"""C004: preregistered structural/operator-centrality gate, no beta search."""
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import networkx as nx

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'
SOURCE = 'scf_separator_coverage.json'


def claws(graph):
    return [[c,*sorted(leaves)] for c in sorted(graph)
            for leaves in itertools.combinations(sorted(graph.neighbors(c)),3)
            if graph.subgraph(leaves).number_of_edges() == 0]


def criterion(graph,s,left,right):
    """List exactly the claws spanning both anticomplete outside sides."""
    left,right = set(left)-set(s),set(right)-set(s)
    assert left and right and not any(graph.has_edge(x,y) for x in left for y in right)
    found = set()
    for center in s:
        nl,nr = set(graph[center])&left,set(graph[center])&right
        for first,second in ((nl,nr),(nr,nl)):
            for a,b in itertools.combinations(sorted(first),2):
                if not graph.has_edge(a,b):
                    for c in second:
                        found.add((center,*sorted((a,b,c))))
        for x in nl:
            for y in nr:
                for t in set(graph[center])&set(s):
                    if not graph.has_edge(x,t) and not graph.has_edge(y,t):
                        found.add((center,*sorted((x,y,t))))
    return [list(row) for row in sorted(found)]


def describe(label,code,boundary):
    graph = nx.from_graph6_bytes(code.encode())
    s,left,right = (boundary[k] for k in ('separator','left','right'))
    pairs = boundary.get('pairs',[boundary.get('pair')])
    assert len(pairs) == 1
    u,v = pairs[0]
    assert sorted(tuple(sorted(e)) for e in nx.non_edges(graph.subgraph(s))) == [(u,v)]
    parity = {side:[{'vertex':z,'uv_neighbors':[int(graph.has_edge(z,t)) for t in (u,v)],
                    'J_odd':graph.has_edge(z,u) != graph.has_edge(z,v)}
                   for z in sorted(set(boundary[side])-set(s))] for side in ('left','right')}
    central = {side:not any(item['J_odd'] for item in items) for side,items in parity.items()}
    local = {side:claws(graph.subgraph(boundary[side])) for side in ('left','right')}
    cross = criterion(graph,s,left,right)
    global_claws = claws(graph)
    assert sorted({tuple(c) for rows in list(local.values())+[cross] for c in rows}) == list(map(tuple,global_claws))
    return {'label':label,'graph6':code,'boundary':{'separator':s,'pair':[u,v],'left':left,'right':right},
            'parity':parity,'J_central':central,'local_claws':local,'cross_claws':cross,
            'global_claw_free':not global_claws}


def exhaustive():
    s,left,right = [0,1,2],[0,1,2,3,4],[0,1,2,5,6]
    fixed = [(0,2),(1,2)]
    free = [(x,y) for x in s for y in range(3,7)]+[(3,4),(5,6)]
    assert len(free) == 14
    counts = Counter()
    truth = bytearray()
    for mask in range(1 << len(free)):
        graph = nx.Graph()
        graph.add_nodes_from(range(7))
        graph.add_edges_from(fixed+[e for i,e in enumerate(free) if mask >> i & 1])
        local_ok = not claws(graph.subgraph(left)) and not claws(graph.subgraph(right))
        cross_ok = not criterion(graph,s,left,right)
        accepted = local_ok and cross_ok
        truth.append(int(accepted))
        counts['graphs'] += 1
        counts['locally_claw_free'] += local_ok
        counts['predicted_globally_claw_free'] += accepted
        counts['local_pass_cross_fail'] += local_ok and not cross_ok
    return {'free_edges':free,'fixed_edges':fixed,'counts':dict(counts),
            'acceptance_bitstream_sha256':hashlib.sha256(truth).hexdigest()}


def main():
    raw=(DATA/SOURCE).read_bytes().replace(b'\r\n',b'\n')
    source=json.loads(raw)
    records=[describe(r['label'],r['graph6'],r['best']) for r in source['records'] if r['minimum_pair_events']==1]
    assert len(records)==36 and len({r['graph6'] for r in records})==35
    assert all(r['global_claw_free'] for r in records)
    controls=[]
    for n,s,left,right in [(4,[0,2],[0,1,2],[0,2,3]),(5,[0,2],[0,1,2],[0,2,3,4])]:
        code=nx.to_graph6_bytes(nx.cycle_graph(n),header=False).decode().strip()
        controls.append(describe('C'+str(n),code,{'separator':s,'pairs':[[0,2]],'left':left,'right':right}))
    g8=json.loads((DATA/'almost_clique_closure_counterexample.json').read_text())
    controls.append(describe('published_G8',g8['graph6'],g8['boundary']))
    report={'experiment':'C004_cross_claw_and_central_sector_gate','date':'2026-09-06',
            'preregistration_commit':'a3766c3','source_sha256':hashlib.sha256(raw).hexdigest(),
            'weighted_rows':len(records),'distinct_graphs':35,
            'central_side_histogram':dict(Counter(str(sum(r['J_central'].values())) for r in records)),
            'quantum_compatibility_proved':False,'SCF_conjecture_falsified':False,
            'status':'structural_gate_only_operator_compatibility_unresolved',
            'controls':controls,'records':records,'exhaustive_template':exhaustive(),
            'dephasing_control':{'pauli_words':['XI','ZX','IZ','IX','YZ'],
                'weights':[1,1,1,3,1],'pair':[0,2],'J_word':'XZ',
                'coherent_integer_state':[1,1,1,1],'sector_integer_state':[1,0,1,0],
                'coherent_expectations':['1','0','0','1','0'],
                'sector_expectations':['1','0','1','0','0'],
                'exact_coherent_value':4,'exact_sector_optimum':2,'exact_stable_bound':4}}
    (DATA/'scf_cross_claw_gate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('records','controls')}))


if __name__=='__main__':
    if not __debug__: raise RuntimeError('Assertions required.')
    main()
