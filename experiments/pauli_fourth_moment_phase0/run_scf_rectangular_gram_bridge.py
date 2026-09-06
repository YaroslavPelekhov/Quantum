"""C005: exact signed rectangular Gram bridge; no numerical optimization."""
import hashlib
import itertools
import json
from pathlib import Path
import networkx as nx
import sympy as sp
from run_scf_gram_completion import product,transfer_coefficients,check_envelope

DATA=Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def family(m):
    cells=[(r,j) for j in range(m+1) for r in (0,1)]+[(2,0),(0,m+1),(1,m+2)]
    n=len(cells)+3
    h0,h1,hc=range(n-3,n)
    graph=nx.Graph()
    graph.add_nodes_from(range(n))
    graph.add_edges_from((i,j) for i,j in itertools.combinations(range(len(cells)),2)
                         if cells[i][0]==cells[j][0] or cells[i][1]==cells[j][1])
    graph.add_edges_from(itertools.combinations((h0,h1,hc),2))
    for i,(r,c) in enumerate(cells):
        for h,commutes in ((h0,r==0),(h1,r==1),(hc,c==0)):
            if not commutes: graph.add_edge(h,i)
    return graph,cells,[h0,h1,hc]


def phases(graph,heavy,m):
    result=[]
    for j in range(m+1):
        word,phase=(),-1
        for v in (heavy[0],heavy[1],2*j,2*j+1):
            word,sign=product(graph,word,(v,))
            phase*=sign
        result.append({'word':list(word),'phase':phase})
    return result


def reduced(expression,a,k):
    out={}
    for powers,c in sp.Poly(sp.expand(expression),*(a+k)).terms():
        key=(powers[:len(a)],tuple(p%2 for p in powers[len(a):]))
        out[key]=out.get(key,0)+int(c)
    return {key:c for key,c in out.items() if c}


def record(m):
    graph,cells,heavy=family(m)
    n=len(graph)
    a=sp.symbols(f'a0:{n}')
    k=sp.symbols(f'k0:{m+1}')
    centers=phases(graph,heavy,m)
    mapping={}
    for mask in range(1<<(m+1)):
        word,phase=(),1
        for j,c in enumerate(centers):
            if mask>>j&1:
                word,sign=product(graph,word,tuple(c['word']))
                phase*=sign*c['phase']
        assert word not in mapping
        mapping[word]=(mask,phase)
    coeff=transfer_coefficients(graph)
    spectral=[]
    for terms in coeff:
        val=0
        for (word,powers),c in terms.items():
            mask,phase=mapping[word]
            val+=c*phase*sp.prod(v**p for v,p in zip(a,powers))*sp.prod(k[j] for j in range(m+1) if mask>>j&1)
        spectral.append(val)
    B=sp.zeros(3,m+3)
    tokens=[[None]*(m+3) for _ in range(3)]
    for i,(r,c) in enumerate(cells):
        center=c if r==1 and c<=m else None
        B[r,c]=a[i]*(k[center] if center is not None else 1)
        tokens[r][c]={'amplitude_vertex':i,'central_index':center}
    M=B*B.T
    second=sum(M.extract(s,s).det() for s in itertools.combinations(range(3),2))
    h0,h1,hc=heavy
    q=sp.Matrix([a[h0],a[h1]])
    heavy_term=(q.T*M[:2,:2]*q)[0]+a[hc]**2*sum(B[r,0]**2 for r in range(3))
    expected=[sp.trace(M)+sum(a[h]**2 for h in heavy),second+heavy_term,M.det()]
    assert all(not reduced(x-y,a,k) for x,y in zip(spectral,expected))
    stored=[[{'word':list(word),'powers':list(powers),'coefficient':c}
             for (word,powers),c in sorted(terms.items())] for terms in coeff]
    return {'m':m,'graph6':nx.to_graph6_bytes(graph,header=False).decode().strip(),
            'light_root_cells':[list(x) for x in cells],'heavy_vertices':heavy,
            'weights':[1]*len(cells)+[2]*3,'central_involutions':centers,
            'Gram_B':tokens,'transfer_coefficients':stored,
            'exact_weighted_bound':3,'all_weights_claim':False,
            'identity_status':'all_three_symbolic_transfer_identities_passed'}


def main():
    check_envelope()
    rows=[record(m) for m in range(6)]
    raw=(DATA/'scf_order10_frontier.json').read_bytes().replace(b'\r\n',b'\n')
    target=json.loads(raw)['representatives'][0]
    f=nx.from_graph6_bytes(rows[1]['graph6'].encode())
    g=nx.from_graph6_bytes(target['graph6'].encode())
    nx.set_node_attributes(f,dict(enumerate(rows[1]['weights'])),'w')
    nx.set_node_attributes(g,dict(enumerate(target['integer_weights'])),'w')
    match=nx.algorithms.isomorphism.GraphMatcher(f,g,node_match=nx.algorithms.isomorphism.categorical_node_match('w',None))
    assert match.is_isomorphic()
    result={'experiment':'C005_rectangular_signed_Gram_transfer_bridge','date':'2026-09-06',
            'preregistration_commit':'1909d6e','source_sha256':hashlib.sha256(raw).hexdigest(),
            'target':target,'family_to_target_mapping':[match.mapping[i] for i in range(10)],
            'finite_audit_m':list(range(6)),'finite_audit_orders':[2*m+8 for m in range(6)],
            'family_fixed_weight_theorem':'proved_by_analytic_transfer_and_Gram_argument; independent verification required',
            'all_weights_claim':False,'unrestricted_SCF_theorem':False,'A_star_confirmed':False,
            'numerical_SDP_used':False,'records':rows}
    (DATA/'scf_rectangular_gram_bridge.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'orders':result['finite_audit_orders'],'target':target['graph6'],
                      'all_coefficient_identities_passed':True,'numerical_SDP_used':False}))


if __name__=='__main__':
    if not __debug__: raise RuntimeError('Assertions required.')
    main()
