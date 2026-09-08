"""C015 independent complex-vector/bitwise Pauli reevaluation (stdlib).

Verifies saved physical witnesses and the ledger, not global optimality
or an independent rerun of every optimizer trajectory.
"""
import hashlib
import json
from verify_scf_two_xx_weight import verify as verify_source,DATA
from verify_scf_generalization import graph_edges


def evaluate(labels,weights,encoded):
    state=[complex(*z) for z in encoded]
    size=len(state);q=size.bit_length()-1
    assert size==1<<q and abs(sum(abs(z)**2 for z in state)-1)<1e-9
    ex=[]
    for x,z in labels:
        assert 0<=x<size and 0<=z<size
        phase=(1j)**((x&z).bit_count()%4)
        value=sum(state[j^x].conjugate()*phase*(-1 if (j&z).bit_count()%2 else 1)*state[j]
                  for j in range(size))
        assert abs(value.imag)<1e-9
        ex.append(value.real)
    return sum(w*e*e for w,e in zip(weights,ex)),ex


def free_coordinates(n,edges):
    # Matrix elimination rather than discovery's dictionary of bit rows.
    M=[[int(tuple(sorted((i,j))) in edges) for j in range(n)] for i in range(n)]
    k=0;pivots=[]
    for j in range(n):
        pivot=next((i for i in range(k,n) if M[i][j]),None)
        if pivot is None:continue
        M[k],M[pivot]=M[pivot],M[k]
        for i in range(n):
            if i!=k and M[i][j]:M[i]=[a^b for a,b in zip(M[i],M[k])]
        pivots.append(j);k+=1
    assert k==14
    return [j for j in range(n) if j not in pivots]


def verify(report):
    assert not any(report[k] for k in ('quantum_target_proved','unrestricted_SCF_theorem','A_star_confirmed'))
    raw=(DATA/'scf_two_xx_weight_c014.json').read_bytes().replace(b'\r\n',b'\n')
    assert hashlib.sha256(raw).hexdigest()==report['source_sha256']
    source=json.loads(raw);verify_source(source)
    n,edges=graph_edges(source['graph6'])
    assert report['free_sign_coordinates']==free_coordinates(n,edges)
    assert report['total_registered_starts']==1024 and 1<=report['batches']<=2
    runs=report['runs']
    assert 0<len(runs)<=1024 and [r['start_index'] for r in runs]==list(range(len(runs)))
    assert all(1<=r['iterations']<=64 and type(r['converged']) is bool and r['value']>=0 for r in runs)
    assert report['best']['value']==max(r['value'] for r in runs)
    if report['status']=='no_violation_in_completed_finite_attack':
        assert len(runs)==1024 and report['best']['value']<=6+1e-7
    elif report['status']=='incomplete_prefix_time_cap':assert len(runs)<1024
    else:
        assert report['status']=='numerical_violation_candidate_not_exact'
        assert report['best']['value']>6+1e-7
    labels=source['standard_SAUR_labels'];w=source['records'][0]['weights']
    best,ex=evaluate(labels,w,report['best']['state'])
    assert abs(best-report['best']['value'])<1e-9
    assert len(ex)==len(report['best']['expectations'])==24
    assert max(abs(a-b) for a,b in zip(ex,report['best']['expectations']))<1e-9
    controls=report['controls'];positive=controls['positive_G8']
    known=json.loads((DATA/'almost_clique_closure_counterexample.json').read_text())
    c_labels=[]
    for word in known['pauli_words']:
        q=len(word)
        c_labels.append([sum(1<<(q-1-j) for j,c in enumerate(word) if c in 'XY'),
                         sum(1<<(q-1-j) for j,c in enumerate(word) if c in 'YZ')])
    assert positive['labels']==c_labels and positive['weights']==known['weights']
    control_value,_=evaluate(c_labels,known['weights'],positive['state'])
    assert abs(control_value-positive['value'])<1e-9 and control_value>3.03
    assert positive['exact_stable_bound']==3 and positive['starts']==128
    low=controls['stable_lower_bound']
    assert low['stable_mask']==source['records'][0]['tight_masks'][0]
    lower,lex=evaluate(labels,w,low['state'])
    assert abs(lower-6)<1e-9 and abs(lower-low['value'])<1e-9
    assert all(abs(lex[i]*lex[i]-1)<1e-9 for i in range(24) if low['stable_mask']>>i&1)
    double=controls['double_weight_control']
    double_value,_=evaluate(labels,source['records'][1]['weights'],double['state'])
    assert abs(double_value-double['value'])<1e-9 and double_value<=7+1e-8
    assert controls['dense_operator_checks_passed']
    assert controls['theta_numerical_relaxation']>=6-1e-5
    assert len(controls['proposal_profile'])==24 and min(controls['proposal_profile'])>=0
    return dict(status='C015_saved_witnesses_and_scope_independently_verified',
                completed_starts=len(runs),registered_starts=1024,best_reevaluated=best,
                positive_G8_reevaluated=control_value,double_control_reevaluated=double_value,
                all_trajectories_independently_replayed=False,quantum_target_proved=False,
                unrestricted_SCF_theorem=False,A_star_confirmed=False)


if __name__=='__main__':
    if not __debug__:raise RuntimeError('Assertions required')
    print(json.dumps(verify(json.loads((DATA/'scf_two_xx_attack_c015.json').read_text()))))
