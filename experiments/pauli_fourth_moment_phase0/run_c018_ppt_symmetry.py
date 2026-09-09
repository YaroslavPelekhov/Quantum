"""C018 exact affine/linear orbit reduction, followed by bounded LP."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
import networkx as nx
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits

Q=7
D=128
N=D*D


def parity(v):return ((v&(D-1))&(v>>Q)).bit_count()%2


def sp(a,b):return (((a&(D-1))&(b>>Q)).bit_count()+((a>>Q)&(b&(D-1))).bit_count())%2


def apply(v,cols):
    out=0
    while v:
        bit=v&-v;out^=cols[bit.bit_length()-1];v^=bit
    return out


def induced(labels,perm):
    basis={}
    for i,v in enumerate(labels):
        image=labels[perm[i]]
        while v:
            bit=v.bit_length()-1
            if bit not in basis:
                basis[bit]=(v,image);break
            v^=basis[bit][0];image^=basis[bit][1]
        if not v and image:return None
    if len(basis)!=14:return None
    cols=[]
    for bit in range(14):
        v=1<<bit;image=0
        while v:
            j=v.bit_length()-1;v^=basis[j][0];image^=basis[j][1]
        cols.append(image)
    assert all(apply(v,cols)==labels[perm[i]] for i,v in enumerate(labels))
    assert all(sp(cols[i],cols[j])==sp(1<<i,1<<j) for i in range(14) for j in range(14))
    linear=sum(parity(v)<<i for i,v in enumerate(cols))
    delta=apply(((linear&(D-1))<<Q)|(linear>>Q),cols)
    mapping=np.array([apply(v,cols) for v in range(N)],dtype=np.int64)
    assert len(set(mapping))==N
    assert all(parity(int(mapping[v])^delta)==parity(v) for v in range(N))
    return cols,delta,mapping


class Orbits:
    def __init__(self):self.parent=list(range(N))
    def root(self,a):
        while self.parent[a]!=a:
            self.parent[a]=self.parent[self.parent[a]];a=self.parent[a]
        return a
    def add(self,mapping):
        for a,b in enumerate(mapping):
            ra,rb=self.root(a),self.root(int(b))
            if ra!=rb:self.parent[rb]=ra
    def groups(self):
        groups={}
        for i in range(N):groups.setdefault(self.root(i),[]).append(i)
        return list(groups.values())


def integer_transform(p):
    idx=np.arange(N);out=p.copy()
    for j in range(Q):
        bits=(1<<j)|(1<<(Q+j));base=idx&~bits;old=out;out=np.zeros(N,dtype=np.int64)
        for a in range(4):
            neighbor=base|((a&1)<<j)|((a>>1)<<(Q+j))
            out+=np.where(((idx^neighbor)&bits)==bits,-1,1)*old[neighbor]
    return out


def run():
    started=time.monotonic()
    source=json.loads(Path('results/pauli_fourth_moment_phase0/scf_two_xx_weight_c014.json').read_text())
    g=nx.from_graph6_bytes(source['graph6'].encode());w=source['records'][0]['weights']
    for i in g:g.nodes[i]['weight']=w[i]
    labels=[x|(z<<Q) for x,z in source['standard_SAUR_labels']]
    c=np.array([sum(weight*(-1)**(parity(p)+sp(v,p)) for weight,p in zip(w,labels)) for v in range(N)])
    af,li=Orbits(),Orbits();maps=[];rejected=0;complete=True
    gm=nx.algorithms.isomorphism.GraphMatcher(g,g,node_match=lambda a,b:a['weight']==b['weight'])
    for count,perm in enumerate(gm.isomorphisms_iter()):
        if count>=256 or time.monotonic()-started>20:complete=False;break
        result=induced(labels,perm)
        if result is None:rejected+=1;continue
        cols,delta,mapping=result
        assert np.array_equal(c[mapping^delta],c)
        af.add(mapping^delta);li.add(mapping)
        maps.append(dict(permutation=[perm[i] for i in range(24)],columns=cols,delta=delta))
    ag,lg=af.groups(),li.groups();sizes=np.array(list(map(len,ag)));reps=[x[0] for x in lg]
    report=dict(maps=maps,rejected_maps=rejected,enumeration_complete=complete,
                affine_orbits=ag,linear_orbits=lg,variables=len(ag),ppt_constraints=len(lg))
    print(json.dumps({k:v for k,v in report.items() if k not in ('maps','affine_orbits','linear_orbits')}),flush=True)
    if len(ag)*len(lg)>10_000_000:
        report['status']='construction_size_cap';return report,{}
    build=time.monotonic();matrix=np.empty((len(lg),len(ag)),dtype=np.int64)
    for j,group in enumerate(ag):
        assert time.monotonic()-build<60,'construction time cap'
        indicator=np.zeros(N,dtype=np.int64);indicator[group]=1
        transformed=integer_transform(indicator)
        # Verify every constraint orbit, not just its representative.
        assert all(np.all(transformed[group2]==transformed[group2[0]]) for group2 in lg)
        matrix[:,j]=transformed[reps]
    costs=c[[x[0] for x in ag]]
    a=matrix.astype(float)/(D*sizes[None,:])
    result=linprog(-costs,A_ub=-a,b_ub=np.zeros(len(lg)),A_eq=np.ones((1,len(ag))),b_eq=[1],
                   bounds=(0,None),method='highs-ds',options={'time_limit':60,'threads':1})
    report.update(status=int(result.status),message=result.message,seconds=time.monotonic()-started)
    arrays={'integer_matrix':matrix,'sizes':sizes,'costs':costs}
    if result.x is not None:
        lam=np.zeros(N)
        for group,mass in zip(ag,result.x):lam[group]=mass/len(group)
        from run_c017_ppt import transform
        mu=transform(lam,Q)
        report.update(value=float(c@lam),min_lambda=float(min(lam)),min_pt=float(min(mu)),trace=float(sum(lam)))
        arrays.update(C014_lambda=lam,C014_objective=c,orbit_mass=result.x)
    return report,arrays


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    assert not args.output.exists() and not args.output.with_suffix('.npz').exists()
    with threadpool_limits(limits=1):report,arrays=run()
    with args.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    with args.output.with_suffix('.npz').open('xb') as stream:np.savez_compressed(stream,**arrays)
    print(json.dumps({k:v for k,v in report.items() if k not in ('maps','affine_orbits','linear_orbits')},indent=2))
