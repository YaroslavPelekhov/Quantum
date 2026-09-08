"""C015 deterministic, bounded quantum falsification; never a proof by sampling."""
import argparse
import hashlib
import json
import time
import itertools as it
import numpy as np
import cvxpy as cp
import scipy.linalg as sla
from threadpoolctl import threadpool_limits
from verify_scf_xx_gate import DATA
from verify_scf_generalization import graph_edges

I=np.eye(2,dtype=complex)
X=np.array([[0,1],[1,0]],dtype=complex)
Y=np.array([[0,-1j],[1j,0]],dtype=complex)
Z=np.diag([1,-1]).astype(complex)


def matrices(labels,q):
    result=[]
    for x,z in labels:
        p=np.ones((1,1),dtype=complex)
        for j in reversed(range(q)):
            p=np.kron(p,{(0,0):I,(1,0):X,(0,1):Z,(1,1):Y}[((x>>j)&1,(z>>j)&1)])
        result.append(p)
    return np.stack(result)


def complement_coordinates(n,edges):
    basis={}
    for i in range(n):
        row=sum(1<<j for j in range(n) if tuple(sorted((i,j))) in edges)
        while row:
            k=(row & -row).bit_length()-1
            if k not in basis:
                basis[k]=row;break
            row^=basis[k]
    return [j for j in range(n) if j not in basis]


def expectations(ops,state):
    return np.real(ops.reshape(len(ops),-1) @ np.outer(state.conj(),state).reshape(-1))


def encode_state(state):return [[float(v.real),float(v.imag)] for v in state]


def optimize(ops,w,initial,limit):
    root=np.sqrt(w);a=np.array(initial,dtype=float);a/=np.linalg.norm(a)
    best=None;converged=False;fallbacks=0
    for step in range(limit):
        H=((root*a) @ ops.reshape(len(ops),-1)).reshape(ops.shape[1:])
        assert np.all(np.isfinite(H)) and np.max(np.abs(H-H.conj().T))<1e-12
        try:
            ev,U=np.linalg.eigh(H)
        except np.linalg.LinAlgError:
            ev,U=sla.eigh(H,driver='evr',check_finite=True)
            fallbacks+=1
        location=int(np.argmax(np.abs(ev)))
        state=U[:,location]
        assert np.linalg.norm(H@state-ev[location]*state)<1e-8
        exp=expectations(ops,state)
        value=float(w@(exp*exp))
        if best is None or value>best['value']:
            best=dict(value=value,state=encode_state(state),expectations=exp.tolist())
        new=root*exp;norm=np.linalg.norm(new)
        assert norm>1e-14
        new/=norm
        if min(np.linalg.norm(new-a),np.linalg.norm(new+a))<1e-10:
            converged=True;break
        a=new
    best.update(iterations=step+1,converged=converged,eigensolver_fallbacks=fallbacks)
    return best


def theta_profile(n,edges,w):
    M=cp.Variable((n+1,n+1),symmetric=True)
    cons=[M>>0,M[0,0]==1]
    cons += [M[i+1,i+1]==M[0,i+1] for i in range(n)]
    cons += [M[i+1,j+1]==0 for i,j in edges]
    prob=cp.Problem(cp.Maximize(w@cp.diag(M)[1:]),cons)
    prob.solve(solver='CLARABEL')
    assert prob.status in ('optimal','optimal_inaccurate')
    return float(prob.value),np.maximum(np.diag(M.value)[1:],0)


def setup(source,ops,w,edges):
    assert all(np.array_equal(p,p.conj().T) and np.array_equal(p@p,np.eye(len(p))) for p in ops)
    assert all(np.array_equal(ops[i]@ops[j],(-1 if (i,j) in edges else 1)*(ops[j]@ops[i]))
               for i,j in it.combinations(range(24),2))
    control=json.loads((DATA/'almost_clique_closure_counterexample.json').read_text())
    q=len(control['pauli_words'][0]);labels=[]
    for word in control['pauli_words']:
        labels.append([sum((1<<(q-1-j)) for j,c in enumerate(word) if c in 'XY'),
                       sum((1<<(q-1-j)) for j,c in enumerate(word) if c in 'ZY')])
    c_ops=matrices(labels,q);cw=np.array(control['weights'],dtype=float)
    c_runs=[optimize(c_ops,cw,[1]+[-1 if mask>>(j-1)&1 else 1 for j in range(1,8)],160)
            for mask in range(128)]
    positive=max(c_runs,key=lambda r:r['value'])
    assert positive['value']>3.03
    positive.update(labels=labels,weights=control['weights'],exact_stable_bound=3,starts=128)
    state=np.eye(len(ops[0]),dtype=complex)[:,0]
    tight=source['records'][0]['tight_masks'][0]
    for i in range(24):
        if tight>>i&1:
            trial=state+ops[i]@state
            if np.linalg.norm(trial)<1e-12:trial=state-ops[i]@state
            state=trial/np.linalg.norm(trial)
    value=float(w@(expectations(ops,state)**2))
    assert abs(value-6)<1e-10
    lower=dict(value=value,state=encode_state(state),stable_mask=tight)
    cw=np.array(source['records'][1]['weights'],dtype=float)
    other=[optimize(ops,cw,[(-1 if mask>>j&1 else 1) for j in range(24)],64) for mask in range(16)]
    best_other=max(other,key=lambda r:r['value'])
    assert best_other['value']<=7+1e-8
    upper,profile=theta_profile(24,edges,w)
    return dict(positive_G8=positive,stable_lower_bound=lower,
                double_weight_control=best_other,theta_numerical_relaxation=upper,
                proposal_profile=profile.tolist(),dense_operator_checks_passed=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    started=time.monotonic()
    source_path=DATA/'scf_two_xx_weight_c014.json'
    raw=source_path.read_bytes().replace(b'\r\n',b'\n');source=json.loads(raw)
    n,edges=graph_edges(source['graph6']);assert n==24
    w=np.array(source['records'][0]['weights'],dtype=float)
    ops=matrices(source['standard_SAUR_labels'],7)
    free=complement_coordinates(n,edges);assert len(free)==10
    path=DATA/'scf_two_xx_attack_c015.json'
    with threadpool_limits(limits=1):
        if args.resume:
            result=json.loads(path.read_text())
            assert result['source_sha256']==hashlib.sha256(raw).hexdigest()
            assert result['free_sign_coordinates']==free and result['batches']<2
            if result['status']=='running':
                result['recovered_aborted_checkpoint']=dict(completed_starts=len(result['runs']),
                    reason='prior numpy eigh nonconvergence; replay from last saved prefix with EVR fallback')
            result['batches']+=1
        else:
            assert not path.exists(), 'Use explicit --resume for an existing attack artifact'
            result=dict(experiment='C015_two_XX_frozen_quantum_attack',preregistration_commit='832dcc8',
                        source_sha256=hashlib.sha256(raw).hexdigest(),free_sign_coordinates=free,
                        total_registered_starts=1024,batches=1,controls=setup(source,ops,w,edges),
                        runs=[],best=None,status='running',quantum_target_proved=False,
                        unrestricted_SCF_theorem=False,A_star_confirmed=False)
        initial=np.sqrt(w*np.array(result['controls']['proposal_profile']))
        def save():path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        for mask in range(len(result['runs']),1024):
            if time.monotonic()-started>275:break
            signs=np.ones(n)
            for k,j in enumerate(free):
                if mask>>k&1:signs[j]=-1
            r=optimize(ops,w,initial*signs,64)
            result['runs'].append(dict(start_index=mask,value=r['value'],iterations=r['iterations'],
                                      converged=r['converged'],eigensolver_fallbacks=r['eigensolver_fallbacks']))
            if result['best'] is None or r['value']>result['best']['value']:
                result['best']=dict(start_index=mask,**r)
            if r['value']>6+1e-7:
                result['status']='numerical_violation_candidate_not_exact';save();break
            if (mask+1)%64==0:
                save();print(json.dumps(dict(completed=mask+1,best=result['best']['value'])),flush=True)
        if result['status']!='numerical_violation_candidate_not_exact':
            result['status']='no_violation_in_completed_finite_attack' if len(result['runs'])==1024 else 'incomplete_prefix_time_cap'
        result['last_batch_seconds']=time.monotonic()-started
        save()
        print(json.dumps(dict(status=result['status'],completed=len(result['runs']),
                              best=result['best']['value'] if result['best'] else None,
                              theta=result['controls']['theta_numerical_relaxation'])),flush=True)


if __name__=='__main__':main()
