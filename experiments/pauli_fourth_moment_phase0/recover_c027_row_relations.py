"""Rational recovery of row relations, with full integer equality checks."""
import json
import argparse
from fractions import Fraction
import math
import numpy as np
from scipy.linalg import lstsq
from threadpoolctl import threadpool_limits
from c020_exact_certificate import DATA


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--fraction',action='store_true');args=parser.parse_args()
    output=DATA/('c027_row_relations_fraction.json' if args.fraction else 'c027_row_relations.json')
    assert not output.exists()
    with np.load(DATA/'c027_equality_rank.npz',allow_pickle=False) as data:
        a=data['matrix'].astype(np.int64);b=data['rhs'];p=data['pivots']
    info=json.loads((DATA/'c027_equality_rank.json').read_text())
    rank=info['numerical_ranks']['1e-10'];keep=p[:rank];drop=p[rank:]
    with threadpool_limits(limits=1):
        coeff=lstsq(a[keep].T.astype(float),a[drop].T.astype(float),lapack_driver='gelsy')[0].T
    attempts=[];report=dict(status='no_exact_relations',attempts=attempts)
    denominators=(1,2,4,8,16,32,64,128,256,512,1024)
    recovered=None
    if args.fraction:
        vals=[Fraction(float(v)).limit_denominator(4096) for v in coeff.flat]
        den=math.lcm(*(v.denominator for v in vals))
        if den*max(1,float(np.max(np.abs(coeff))))>1e6:
            denominators=();report.update(status='fraction_resource_cap',denominator_bits=den.bit_length())
        else:
            recovered=np.array([v.numerator*(den//v.denominator) for v in vals],dtype=np.int64).reshape(coeff.shape)
            denominators=(den,)
    for den in denominators:
        assert np.max(np.abs(coeff))*den<1e6
        nums=recovered if recovered is not None else np.rint(coeff*den).astype(np.int64)
        assert int(np.max(np.abs(nums)))*len(keep)*max(int(np.max(np.abs(a))),int(np.max(np.abs(b))))<2**62
        residual=nums@a[keep]-den*a[drop];rhs=nums@b[keep]-den*b[drop]
        accepted=not np.any(residual) and not np.any(rhs)
        attempts.append(dict(denominator=den,max_matrix_residual=int(np.max(np.abs(residual))),
                             max_rhs_residual=int(np.max(np.abs(rhs))),accepted=accepted))
        if accepted:
            report.update(status='exact_redundancy_verified',retained_rows=keep.tolist(),
                          deleted_rows=drop.tolist(),denominator=den,numerators=nums.tolist(),
                          remaining_independence_proved=False,exact_six_proved=False)
            break
    with output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ('retained_rows','deleted_rows','numerators')},indent=2))
