"""C016 exact rational positive-definite matrix and source-degree audit."""
from collections import Counter
from fractions import Fraction as F
import json
from verify_scf_two_xx_gate import DATA,expected_graph
from verify_scf_generalization import graph_edges


def positive_ldl(matrix):
    n=len(matrix);L=[[F(0) for _ in range(n)] for _ in range(n)];D=[]
    for j in range(n):
        d=matrix[j][j]-sum(L[j][k]**2*D[k] for k in range(j))
        assert d>0, 'nonpositive exact LDL pivot'
        D.append(d);L[j][j]=F(1)
        for i in range(j+1,n):
            L[i][j]=(matrix[i][j]-sum(L[i][k]*L[j][k]*D[k] for k in range(j)))/d
    assert all(matrix[i][j]==sum(L[i][k]*D[k]*L[j][k] for k in range(n))
               for i in range(n) for j in range(n))
    return D


def verify(report):
    assert not any(report[k] for k in ('physical_state_claim','quantum_target_proved',
                                       'unrestricted_SCF_theorem','A_star_confirmed'))
    _,edges=expected_graph();assert graph_edges(report['graph6'])==(24,edges)
    assert report['weights']==[1+int(i in (6,7)) for i in range(24)]
    den=report['denominator'];assert den==100000000
    raw=report['moment_numerators']
    assert len(raw)==25 and all(len(row)==25 and all(type(x) is int for x in row) for row in raw)
    M=[[F(x,den) for x in row] for row in raw]
    assert all(M[i][j]==M[j][i] for i in range(25) for j in range(25))
    assert M[0][0]==1 and all(M[0][i]==M[i][i] for i in range(1,25))
    assert all(M[i+1][j+1]==0 for i,j in edges)
    D=positive_ldl(M)
    objective=sum(w*M[i+1][i+1] for i,w in enumerate(report['weights']))
    assert objective==F(report['objective']) and objective>6
    assert report['interior_weight']=='1/1000' and report['interior_diagonal']=='1/48'
    histogram=Counter(sum(i in e for e in edges) for i in range(24))
    assert {int(k):v for k,v in report['degree_histogram'].items()}==histogram
    # Published gear: the union of the two explicitly defined 5-wheels.
    gear=set()
    for h,cycle in [('h1',['a','d1','b1','c','h2']),('h2',['a','d2','b2','c','h1'])]:
        gear|={tuple(sorted((h,v))) for v in cycle}
        gear|={tuple(sorted((cycle[i],cycle[(i+1)%5]))) for i in range(5)}
    assert all(sum(h in e for e in gear)==5 for h in ('h1','h2'))
    assert report['ordinary_gear_hub_required_degree']==5 and 5 not in histogram
    return dict(status='C016_exact_positive_definite_theta_witness_verified',
                dimension=25,positive_pivots=len(D),exact_objective=str(objective),exact_gap=str(objective-6),
                no_degree_five_vertex=True,direct_ordinary_gear_output_excluded=True,
                general_classical_strip_theorems_excluded=False,physical_state_claim=False,
                quantum_target_proved=False,A_star_confirmed=False)


if __name__=='__main__':
    if not __debug__:raise RuntimeError('Assertions required')
    print(json.dumps(verify(json.loads((DATA/'scf_two_xx_baseline_c016.json').read_text()))))
