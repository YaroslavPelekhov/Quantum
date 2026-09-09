"""Build then independently verify a rational PPT witness; verify uses stdlib."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

DATA=Path('results/pauli_fourth_moment_phase0')
SOURCE=DATA/'scf_two_xx_weight_c014.json'


def pt_integer(values):
    out=values[:]
    for bit in range(7):
        old=out;out=[];mask=(1<<bit)|(1<<(7+bit))
        for i in range(16384):
            base=i&~mask
            neighbors=[base,base|(1<<bit),base|(1<<(7+bit)),base|mask]
            out.append(sum((-v if (i^j)&mask==mask else v) for j,v in ((j,old[j]) for j in neighbors)))
    return out


def walsh(values):
    a=values[:];width=1
    while width<len(a):
        for base in range(0,len(a),2*width):
            for j in range(width):
                left,right=a[base+j],a[base+j+width]
                a[base+j]=left+right;a[base+j+width]=left-right
        width*=2
    return a


def objective(source):
    # Tensor products of the explicitly known one-pair Bell eigenvalues.
    local=((1,1,1,1),(1,1,-1,-1),(1,-1,1,-1),(-1,1,1,-1))
    result=[]
    for v in range(16384):
        total=0
        for (x,z),weight in zip(source['standard_SAUR_labels'],source['records'][0]['weights']):
            val=weight
            for j in range(7):
                p=((x>>j)&1)+2*((z>>j)&1)
                b=((v>>j)&1)+2*((v>>(j+7))&1)
                val*=local[p][b]
            total+=val
        result.append(total)
    return result


def verify(cert):
    assert cert['source_sha256']==hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    p=cert['numerators'];den=cert['denominator']
    assert len(p)==16384 and all(type(v) is int and v>=0 for v in p)
    assert type(den) is int and den==sum(p)>0
    mu=pt_integer(p)
    assert min(mu)>=0 and sum(mu)==128*den
    # Different exact algorithm for ALL PT coordinates.
    freq=walsh(p)
    freq=[(-v if ((i%128)&(i//128)).bit_count()%2 else v) for i,v in enumerate(freq)]
    second=walsh(freq)
    assert second==[128*v for v in mu]
    c=objective(json.loads(SOURCE.read_text()))
    value=Fraction(sum(a*b for a,b in zip(c,p)),den)
    assert str(value)==cert['exact_value'] and value>6
    assert min(mu)==cert['min_pt_numerator']
    return dict(exact_value=str(value),decimal_value=float(value),strict_gap=str(value-6),
                probabilities_verified=len(p),pt_coordinates_verified=len(mu),
                min_probability_numerator=min(p),min_pt_numerator=min(mu),
                PPT_route_to_six_excluded=True,physical_violation=False,
                quantum_target_proved=False)


def build(path):
    import numpy as np
    with np.load(DATA/'c020_ppt_primal.npz',allow_pickle=False) as data:
        p=[max(0,int(round(float(v)*10**12))) for v in data['probabilities']]
    mu=pt_integer(p);shift=max(0,(-min(mu)+127)//128)+1
    p=[v+shift for v in p];den=sum(p);mu=pt_integer(p)
    c=objective(json.loads(SOURCE.read_text()))
    cert=dict(source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),numerators=p,
              denominator=den,min_pt_numerator=min(mu),
              exact_value=str(Fraction(sum(a*b for a,b in zip(c,p)),den)),
              scope='PPT feasible state, not separable/product witness')
    verify(cert)
    with path.open('x',encoding='utf-8') as stream:json.dump(cert,stream,indent=2)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('build','verify'));args=parser.parse_args()
    path=DATA/'c020_exact_ppt_certificate.json'
    if args.mode=='build':build(path)
    print(json.dumps(verify(json.loads(path.read_text())),indent=2))
