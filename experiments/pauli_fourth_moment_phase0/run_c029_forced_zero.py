"""One equality-only exposing-vector test with exact acceptance."""
from fractions import Fraction
import json
import math
import time
import numpy as np
from scipy.linalg import lstsq
from threadpoolctl import threadpool_limits
from c020_exact_certificate import DATA
from verify_c027_row_relations import verify


if __name__=='__main__':
    path=DATA/'c029_forced_zero.json';assert not path.exists();start=time.monotonic()
    cert=json.loads((DATA/'c027_row_relations_fraction.json').read_text());verify(cert)
    face=json.loads((DATA/'c025_exact_face.json').read_text())
    orbits=json.loads((DATA/'c018_ppt_symmetry.json').read_text())
    zero=set(face['forced_zero_coordinates']);groups=[g for g in orbits['linear_orbits'] if not set(g)&zero]
    with np.load(DATA/'c021_bosonic_ppt.npz',allow_pickle=False) as data:u=-data['C014_dual']
    target=np.array([int(float(np.mean(u[g]))<=1e-8) for g in groups],dtype=np.int64)
    assert sum(target)==63
    with np.load(DATA/'c027_equality_rank.npz',allow_pickle=False) as data:
        a=data['matrix'][cert['retained_rows']].astype(np.int64);b=data['rhs'][cert['retained_rows']]
    system=np.vstack((a.T,b));rhs=np.r_[target,0]
    with threadpool_limits(limits=1):
        y=lstsq(system.astype(float),rhs.astype(float),lapack_driver='gelsy')[0]
    residual=float(np.max(np.abs(system@y-rhs)))
    report=dict(target_orbits=int(sum(target)),max_projection_residual=residual,
                status='no_exact_exposing_functional',exact_zero_extension_proved=False)
    if residual<=1e-9:
        vals=[Fraction(float(v)).limit_denominator(4096) for v in y]
        den=math.lcm(*(v.denominator for v in vals));nums=[v.numerator*(den//v.denominator) for v in vals]
        bound=max(map(abs,nums))*system.shape[1]*int(np.max(np.abs(system)))
        if bound>=2**62 or den>=2**62:report['status']='integer_resource_cap'
        else:
            exact=system@np.array(nums,dtype=np.int64)-den*rhs
            report.update(denominator=den,max_integer_residual=int(np.max(np.abs(exact))))
            if not np.any(exact):
                report.update(status='exact_exposing_functional',exact_zero_extension_proved=True,
                              numerators=nums,target=target.tolist())
    report['seconds']=time.monotonic()-start
    with path.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ('numerators','target')},indent=2))
