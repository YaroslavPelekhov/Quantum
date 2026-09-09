"""Exact rational acceptance of a derived fixed-point filter; no eigensolver."""
from fractions import Fraction as F
import json


def verify(a,b):
    norm=a*a+b*b
    v=[a,0,0,0,0,0,0,b]
    rho=[[F(x*y,norm) for y in v] for x in v]
    # For positive GHZ amplitudes, sqrt(R_C) and pinv(sqrt(M_BC))
    # cancel on b=c; on b!=c the latter is zero. Thus T=I_A tensor Pi_BC.
    diagonal=[int((i//2)%2 == i%2) for i in range(8)]
    updated=[[diagonal[i]*rho[i][j]*diagonal[j] for j in range(8)] for i in range(8)]
    assert updated==rho
    assert sum(rho[i][i] for i in range(8))==1
    assert [[sum(rho[i][k]*rho[k][j] for k in range(8)) for j in range(8)] for i in range(8)]==rho
    m=[[sum(rho[4*k+i][4*k+j] for k in range(2)) for j in range(4)] for i in range(4)]
    r=[[sum(m[2*k+i][2*k+j] for k in range(2)) for j in range(2)] for i in range(2)]
    target=[[F(i//2==j//2,2)*r[i%2][j%2] for j in range(4)] for i in range(4)]
    defect=sum((m[i][j]-target[i][j])**2 for i in range(4) for j in range(4))
    assert defect==F(a**4+b**4,2*norm**2)>0
    return dict(amplitudes=[a,b],fixed=True,causal=False,residual_squared=str(defect))


if __name__=='__main__':
    print(json.dumps(dict(exact=[verify(1,1),verify(1,2)],
                         scope='derived filter fixed points, not author implementation'),indent=2))
