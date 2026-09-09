"""Exact acceptance/rejection of preregistered rational recovery candidates."""
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from c020_exact_certificate import DATA,SOURCE,objective,pt_integer
from c021_exact_dual import verify


def run(stem='c022'):
    import numpy as np
    report=json.loads((DATA/f'{stem}_exact_six.json').read_text())
    with np.load(DATA/f'{stem}_exact_six.npz',allow_pickle=False) as data:
        if 'dual' not in data:return dict(attempts=[],status='no_solver_candidate')
        raw=data['dual'].copy()
    c=objective(json.loads(SOURCE.read_text()));even=[i for i in range(16384) if not ((i%128)&(i//128)).bit_count()%2]
    attempts=[]
    for mode in [1,2,4,8,16,32,64,128,256,512,1024,'bounded_fraction']:
        if mode=='bounded_fraction':
            vals=[Fraction(float(v)).limit_denominator(10000) for v in raw]
            den=math.lcm(*(v.denominator for v in vals))
            if den.bit_length()>4096:
                attempts.append(dict(mode=mode,status='denominator_resource_cap',bits=den.bit_length()));continue
            u=[max(0,v.numerator*(den//v.denominator)) for v in vals]
        else:
            den=mode;u=[max(0,int(round(float(v)*den))) for v in raw]
        transformed=pt_integer(u)
        upper=Fraction(max(c[i]*128*den+transformed[i] for i in even),128*den)
        attempts.append(dict(mode=mode,exact_upper=str(upper),decimal_upper=float(upper),accepted=upper==6))
        if upper==6:
            certificate=dict(source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                             dual_numerators=u,dual_denominator=den,exact_upper='6',symmetric_support_required=True)
            verify(certificate)
            with (DATA/f'{stem}_exact_six_certificate.json').open('x',encoding='utf-8') as stream:json.dump(certificate,stream,indent=2)
            return dict(status='exact_six_verified',attempts=attempts)
    return dict(status='no_exact_six_recovered',attempts=attempts)


if __name__=='__main__':
    result=run()
    with (DATA/'c022_recovery.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result,indent=2))
