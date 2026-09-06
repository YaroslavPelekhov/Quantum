"""C005 acceptance using only integer/Fraction polynomials and word rewriting.

No graph library, SymPy, numerical matrix, or solver is used. Full transfer
coefficients are recomputed, including odd orders, independently of discovery.
"""
from fractions import Fraction as F
import hashlib
import itertools
import json
from pathlib import Path
from verify_scf_generalization import graph_edges,stable
from verify_scf_cross_claw_gate import explicit_claws

DATA=Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


def rewrite(left,right,edges):
    letters=list(left)+list(right)
    sign=1
    i=0
    while i<len(letters)-1:
        if letters[i]==letters[i+1]:
            del letters[i:i+2]
            i=max(0,i-1)
        elif letters[i]>letters[i+1]:
            if (letters[i+1],letters[i]) in edges: sign=-sign
            letters[i],letters[i+1]=letters[i+1],letters[i]
            i=max(0,i-1)
        else: i+=1
    return tuple(letters),sign


class Algebra:
    def __init__(self,n,edges): self.n,self.edges=n,edges
    def constant(self,c): return {((),(0,)*self.n):c} if c else {}
    def variable(self,i): return {((),tuple(int(j==i) for j in range(self.n))):1}
    def add(self,*polys):
        result={}
        for p in polys:
            for key,c in p.items(): result[key]=result.get(key,0)+c
        return {k:c for k,c in result.items() if c}
    def scale(self,p,c): return {k:c*v for k,v in p.items() if c*v}
    def mul(self,p,q):
        out={}
        for (w,a),c in p.items():
            for (v,b),d in q.items():
                word,sign=rewrite(w,v,self.edges)
                key=(word,tuple(x+y for x,y in zip(a,b)))
                out[key]=out.get(key,0)+c*d*sign
        return {k:c for k,c in out.items() if c}
    def sq(self,p): return self.mul(p,p)
    def det(self,matrix):
        n=len(matrix)
        out={}
        for perm in itertools.permutations(range(n)):
            sign=(-1)**sum(perm[i]>perm[j] for i in range(n) for j in range(i+1,n))
            term=self.constant(sign)
            for i,j in enumerate(perm): term=self.mul(term,matrix[i][j])
            out=self.add(out,term)
        return out


def verify_envelope():
    a=Algebra(2,set())
    L,s=a.variable(0),a.variable(1)
    one=a.constant(1)
    y=a.scale(a.sq(s),F(1,6))
    x=a.scale(a.add(L,a.scale(y,-1)),F(1,2))
    E=a.add(a.sq(x),a.scale(a.mul(x,y),2),a.mul(a.add(one,a.scale(L,-2)),y),a.mul(x,s))
    target=a.sq(a.add(a.constant(F(1,4)),a.scale(L,F(1,2))))
    gap=a.scale(a.mul(a.sq(a.add(s,a.constant(-1))),
                      a.add(a.scale(L,12),a.sq(s),a.scale(s,6),a.constant(3))),F(1,48))
    assert a.add(target,a.scale(E,-1),a.scale(gap,-1))=={}


def exact_rank(rows,n):
    matrix=[list(map(F,row)) for row in rows]
    rank=0
    for j in range(n):
        pivot=next((i for i in range(rank,len(matrix)) if matrix[i][j]),None)
        if pivot is None: continue
        matrix[rank],matrix[pivot]=matrix[pivot],matrix[rank]
        scale=matrix[rank][j]
        matrix[rank]=[x/scale for x in matrix[rank]]
        for i in range(rank+1,len(matrix)):
            if matrix[i][j]:
                scale=matrix[i][j]
                matrix[i]=[x-scale*y for x,y in zip(matrix[i],matrix[rank])]
        rank+=1
    return rank


def verify_record(row):
    m=row['m']
    assert isinstance(m,int) and 0<=m<=5
    n,edges=graph_edges(row['graph6'])
    cells=[(r,j) for j in range(m+1) for r in (0,1)]+[(2,0),(0,m+1),(1,m+2)]
    heavy=[len(cells)+i for i in range(3)]
    assert n==2*m+8 and row['light_root_cells']==list(map(list,cells)) and row['heavy_vertices']==heavy
    expected=set(itertools.combinations(heavy,2))
    expected|={(i,j) for i,j in itertools.combinations(range(len(cells)),2)
               if cells[i][0]==cells[j][0] or cells[i][1]==cells[j][1]}
    for i,(r,c) in enumerate(cells):
        for h,commutes in ((heavy[0],r==0),(heavy[1],r==1),(heavy[2],c==0)):
            if not commutes: expected.add((i,h))
    assert edges==expected
    assert not explicit_claws(range(n),edges)
    K={i for i,c in enumerate(cells) if c[1]==0}
    assert len(K)==3 and all(tuple(sorted(e)) in edges for e in itertools.combinations(K,2))
    for v in K:
        outside={i for i in range(n) if i not in K and tuple(sorted((v,i))) in edges}
        assert all(tuple(sorted(e)) in edges for e in itertools.combinations(outside,2))
    weights=[1]*len(cells)+[2]*3
    assert row['weights']==weights and row['exact_weighted_bound']==3 and not row['all_weights_claim']
    independent=[[s for s in itertools.combinations(range(n),k)
                  if not any(pair in edges for pair in itertools.combinations(s,2))] for k in range(5)]
    assert not independent[4] and independent[3]
    assert max(sum(weights[i] for i in s) for group in independent for s in group)==3
    roots=[s for group in independent for s in group if sum(weights[i] for i in s)==3]
    assert exact_rank([[int(i in s) for i in range(n)] for s in roots],n)==n
    assert all(set(s)<=set(range(len(cells))) and 2*(m+1) in s for s in independent[3])
    a=Algebra(n,edges)
    variables=[a.variable(i) for i in range(n)]
    centers=[]
    for j,stored in enumerate(row['central_involutions']):
        word,phase=(),-1
        for v in (heavy[0],heavy[1],2*j,2*j+1):
            word,sign=rewrite(word,(v,),edges)
            phase*=sign
        assert stored=={'word':list(word),'phase':phase}
        assert rewrite(word,word,edges)==((),1)
        assert rewrite(tuple(reversed(word)),(),edges)==(word,1)
        assert all(rewrite(word,(v,),edges)==rewrite((v,),word,edges) for v in range(n))
        centers.append({(word,(0,)*n):phase})
    assert len(centers)==m+1
    B=[[{} for _ in range(m+3)] for _ in range(3)]
    tokens=[[None]*(m+3) for _ in range(3)]
    for i,(r,c) in enumerate(cells):
        index=c if r==1 and c<=m else None
        tokens[r][c]={'amplitude_vertex':i,'central_index':index}
        B[r][c]=a.mul(variables[i],centers[index]) if index is not None else variables[i]
    assert row['Gram_B']==tokens
    M=[[a.add(*(a.mul(B[i][k],B[j][k]) for k in range(m+3))) for j in range(3)] for i in range(3)]
    second=a.add(*(a.det([[M[i][j] for j in pair] for i in pair]) for pair in itertools.combinations(range(3),2)))
    h0,h1,hc=heavy
    hv=[h0,h1]
    heavy_part=a.add(*(a.mul(a.mul(variables[hv[i]],M[i][j]),variables[hv[j]]) for i in range(2) for j in range(2)))
    heavy_part=a.add(heavy_part,a.mul(a.sq(variables[hc]),a.add(*(a.sq(B[i][0]) for i in range(3)))))
    rhs=[a.add(*(M[i][i] for i in range(3)),*(a.sq(variables[i]) for i in heavy)),a.add(second,heavy_part),a.det(M)]
    charges=[]
    for group in independent[:4]:
        charges.append({(s,tuple(int(i in s) for i in range(n))):1 for s in group})
    full=[]
    for degree in range(7):
        full.append(a.add(*(a.scale(a.mul(charges[i],charges[degree-i]),(-1)**i)
                            for i in range(4) if 0<=degree-i<4)))
    assert full[0]==a.constant(1) and all(full[d]=={} for d in (1,3,5))
    for k in range(1,4):
        coeff=a.scale(full[2*k],(-1)**k)
        stored={(tuple(t['word']),tuple(t['powers'])):t['coefficient'] for t in row['transfer_coefficients'][k-1]}
        assert len(stored)==len(row['transfer_coefficients'][k-1])
        assert coeff==stored==rhs[k-1],('transfer_identity',m,k)
    return {'m':m,'vertices':n,'central_involutions':len(centers),
            'facet_root_linear_rank':n,
            'coefficient_terms':[len(p) for p in rhs],'all_identities_exact':True}


def verify(report):
    raw=(DATA/'scf_order10_frontier.json').read_bytes().replace(b'\r\n',b'\n')
    assert hashlib.sha256(raw).hexdigest()==report['source_sha256']
    target=json.loads(raw)['representatives'][0]
    assert report['target']==target
    assert [r['m'] for r in report['records']]==report['finite_audit_m']==list(range(6))
    assert report['finite_audit_orders']==[8,10,12,14,16,18]
    checked=[verify_record(row) for row in report['records']]
    family_row=report['records'][1]
    n,edges=graph_edges(family_row['graph6'])
    nn,target_edges=graph_edges(target['graph6'])
    mapping=report['family_to_target_mapping']
    assert n==nn==10 and sorted(mapping)==list(range(10))
    assert {tuple(sorted((mapping[i],mapping[j]))) for i,j in edges}==target_edges
    assert all(family_row['weights'][i]==target['integer_weights'][mapping[i]] for i in range(10))
    assert not report['all_weights_claim'] and not report['unrestricted_SCF_theorem'] and not report['A_star_confirmed']
    assert not report['numerical_SDP_used']
    verify_envelope()
    return {'status':'exact_rectangular_Gram_bridge_verified','records':checked,'target_exact_beta':3,
            'family_all_weights_claim':False,'unrestricted_SCF_theorem':False}


if __name__=='__main__':
    if not __debug__: raise RuntimeError('Assertions required.')
    print(json.dumps(verify(json.loads((DATA/'scf_rectangular_gram_bridge.json').read_text()))))
