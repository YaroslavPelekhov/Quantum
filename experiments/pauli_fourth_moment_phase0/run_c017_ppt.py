"""Sparse staged Bell-diagonal PPT relaxation; not a physical-state search."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, vstack
from threadpoolctl import threadpool_limits


def local_check():
    i=np.eye(2); x=np.array([[0,1],[1,0]]); z=np.diag([1,-1]); y=np.array([[0,-1j],[1j,0]])
    phi=np.array([1,0,0,1])/np.sqrt(2)
    bell=np.stack([np.kron(i,p)@phi for p in (i,x,z,y)],axis=1)
    actual=[]
    for v in bell.T:
        rho=np.outer(v,v.conj())
        pt=rho.reshape(2,2,2,2).transpose(0,3,2,1).reshape(4,4)
        actual.append(np.real(np.diag(bell.conj().T@pt@bell)))
    expected=np.array([[(-1 if a^b==3 else 1)/2 for b in range(4)] for a in range(4)])
    assert np.max(abs(np.array(actual).T-expected))<1e-12


def transform(p,q):
    n=len(p); idx=np.arange(n); out=p.copy()
    for j in range(q):
        bits=(1<<j)|(1<<(q+j)); base=idx&~bits
        old=out; out=np.zeros(n)
        for a in range(4):
            neighbor=base|((a&1)<<j)|((a>>1)<<(q+j))
            sign=np.where(((idx^neighbor)&bits)==bits,-.5,.5)
            out+=sign*old[neighbor]
    return out


def solve(name,labels,w,q):
    start=time.monotonic(); n=4**q; idx=np.arange(n,dtype=np.int64)
    objective=np.array([sum(weight*(-1)**((x&z).bit_count()+((v&((1<<q)-1))&z).bit_count()+((v>>q)&x).bit_count())
                            for (x,z),weight in zip(labels,w)) for v in range(n)],dtype=float)
    rr=[]; cc=[]; vv=[]
    for j in range(q):
        rows=j*n+idx; bits=(1<<j)|(1<<(q+j)); base=idx&~bits
        rr.append(rows);cc.append((j+1)*n+idx);vv.append(np.ones(n))
        for a in range(4):
            neighbor=base|((a&1)<<j)|((a>>1)<<(q+j))
            sign=np.where(((idx^neighbor)&bits)==bits,-.5,.5)
            rr.append(rows);cc.append(j*n+neighbor);vv.append(-sign)
    mat=coo_matrix((np.concatenate(vv),(np.concatenate(rr),np.concatenate(cc))),shape=(q*n,(q+1)*n)).tocsr()
    trace=coo_matrix((np.ones(n),(np.zeros(n,dtype=int),idx)),shape=(1,(q+1)*n)).tocsr()
    ae=vstack([mat,trace],format='csc'); rhs=np.zeros(q*n+1);rhs[-1]=1
    c=np.zeros((q+1)*n);c[:n]=-objective
    bounds=[(0,None)]*n+[(None,None)]*((q-1)*n)+[(0,None)]*n
    result=linprog(c,A_eq=ae,b_eq=rhs,bounds=bounds,method='highs-ds',options={'time_limit':60,'threads':1})
    report=dict(name=name,q=q,variables=(q+1)*n,equalities=q*n+1,nonzeros=ae.nnz,
                status=int(result.status),message=result.message,seconds=time.monotonic()-start)
    arrays={}
    if result.x is not None:
        p=result.x[:n]; mu=transform(p,q)
        report.update(value=float(objective@p),trace=float(sum(p)),min_probability=float(min(p)),
                      min_pt_probability=float(min(mu)),equality_residual=float(max(abs(ae@result.x-rhs))))
        arrays={name+'_lambda':p,name+'_objective':objective}
        if name=='G8' and result.success:
            assert report['value']>=3.0448-1e-6
    return report,arrays


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    assert not args.output.exists() and not args.output.with_suffix('.npz').exists()
    data=Path('results/pauli_fourth_moment_phase0')
    g=json.loads((data/'almost_clique_closure_counterexample.json').read_text())
    labels=[];q=len(g['pauli_words'][0])
    for word in g['pauli_words']:
        labels.append([sum(1<<(q-1-i) for i,c in enumerate(word) if c in 'XY'),
                       sum(1<<(q-1-i) for i,c in enumerate(word) if c in 'YZ')])
    target=json.loads((data/'scf_two_xx_weight_c014.json').read_text())
    reports=[];arrays={}
    with threadpool_limits(limits=1):
        local_check()
        for name,lab,w,qubits in [('G8',labels,g['weights'],q),('C014',target['standard_SAUR_labels'],target['records'][0]['weights'],7)]:
            report,stored=solve(name,lab,w,qubits)
            reports.append(report);arrays.update(stored)
            print(json.dumps(report),flush=True)
    with args.output.open('x',encoding='utf-8') as stream:json.dump(dict(reports=reports,quantum_target_proved=False),stream,indent=2)
    with args.output.with_suffix('.npz').open('xb') as stream:np.savez_compressed(stream,**arrays)
