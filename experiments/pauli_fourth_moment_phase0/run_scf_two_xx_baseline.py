"""C016 one frozen rational theta witness; not a quantum state."""
from collections import Counter
from fractions import Fraction as F
import json
import time
import numpy as np
import cvxpy as cp
from threadpoolctl import threadpool_limits
from verify_scf_xx_gate import DATA
from verify_scf_generalization import graph_edges


def main():
    started=time.monotonic()
    source=json.loads((DATA/'scf_two_xx_weight_c014.json').read_text())
    n,edges=graph_edges(source['graph6']);w=np.array(source['records'][0]['weights'])
    M=cp.Variable((n+1,n+1),symmetric=True)
    cons=[M>>0,M[0,0]==1]+[M[0,i+1]==M[i+1,i+1] for i in range(n)]
    cons += [M[i+1,j+1]==0 for i,j in edges]
    prob=cp.Problem(cp.Maximize(w@cp.diag(M)[1:]),cons)
    with threadpool_limits(limits=1):prob.solve(solver='CLARABEL')
    assert prob.status in ('optimal','optimal_inaccurate')
    interior=np.zeros((n+1,n+1));interior[0,0]=1
    for i in range(1,n+1):interior[0,i]=interior[i,0]=interior[i,i]=1/48
    mixed=(1-1/1000)*((M.value+M.value.T)/2)+interior/1000
    den=100000000;matrix=np.rint(mixed*den).astype('int64').tolist()
    matrix[0][0]=den
    for i in range(1,n+1):matrix[0][i]=matrix[i][0]=matrix[i][i]
    for i,j in edges:matrix[i+1][j+1]=matrix[j+1][i+1]=0
    objective=F(sum(int(w[i])*matrix[i+1][i+1] for i in range(n)),den)
    result=dict(experiment='C016_exact_theta_baseline_witness',preregistration_commit='689f911',
                graph6=source['graph6'],weights=w.tolist(),denominator=den,moment_numerators=matrix,
                objective=str(objective),interior_weight='1/1000',interior_diagonal='1/48',
                degree_histogram=dict(sorted(Counter(sum(i in e for e in edges) for i in range(n)).items())),
                ordinary_gear_hub_required_degree=5,physical_state_claim=False,
                quantum_target_proved=False,unrestricted_SCF_theorem=False,A_star_confirmed=False)
    assert time.monotonic()-started<300
    (DATA/'scf_two_xx_baseline_c016.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(objective=str(objective),gap=str(objective-6),degree_histogram=result['degree_histogram'])))


if __name__=='__main__':main()
