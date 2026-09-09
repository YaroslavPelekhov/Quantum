"""Exact common-denominator Bell/PPT primal repair, not a dual upper bound."""
from fractions import Fraction
import argparse
import json
from pathlib import Path
import numpy as np


def integer_pt(values,q):
    # No floating point and no sampler transform import. Omits divisor D.
    out=list(map(int,values))
    for bit in range(q):
        old=out
        out=[]
        mask=(1<<bit)|(1<<(q+bit))
        for i in range(len(old)):
            base=i&~mask
            total=0
            for a in range(4):
                j=base|((a&1)<<bit)|((a>>1)<<(q+bit))
                total+=(-1 if (i^j)&mask==mask else 1)*old[j]
            out.append(total)
    return out


def main(path):
    report=json.loads(path.read_text())
    accepted=[]
    with np.load(path.with_suffix('.npz'),allow_pickle=False) as arrays:
        for row in report['reports']:
            name=row['name'];q=row['q'];d=2**q
            if name+'_lambda' not in arrays:
                accepted.append(dict(name=name,certificate_available=False));continue
            p=arrays[name+'_lambda']
            ints=[max(0,int(round(float(v)*10**8))) for v in p]
            numer=integer_pt(ints,q)
            shift=max(0,(-min(numer)+d-1)//d)+1
            ints=[v+shift for v in ints]
            numer=integer_pt(ints,q)
            assert min(ints)>0 and min(numer)>0 and sum(numer)==d*sum(ints)
            # Independent direct character matrix contraction for small control.
            if q<=3:
                expected=[sum((-1)**(((i^j)&(d-1))&((i^j)>>q)).bit_count()*v
                              for j,v in enumerate(ints)) for i in range(len(ints))]
                assert expected==numer
            objective=arrays[name+'_objective']
            assert np.all(objective==np.rint(objective))
            value=Fraction(sum(int(c)*v for c,v in zip(objective,ints)),sum(ints))
            accepted.append(dict(name=name,certificate_available=True,probability_numerators=ints,
                                 denominator=sum(ints),min_pt_numerator=min(numer),pt_denominator=d*sum(ints),
                                 exact_value=str(value),decimal_value=float(value),
                                 interpretation='feasible PPT lower bound on relaxation optimum, NOT physical violation'))
    output=path.with_name(path.stem+'_primal_certificate.json')
    with output.open('x',encoding='utf-8') as stream:json.dump(accepted,stream,indent=2)
    print(json.dumps([{k:v for k,v in row.items() if k!='probability_numerators'} for row in accepted],indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('report',type=Path);args=parser.parse_args();main(args.report)
