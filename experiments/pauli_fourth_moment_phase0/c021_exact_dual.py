"""Exact upper certificate for fixed C014 labels with symmetric-copy PPT.

Build imports NumPy only to read the candidate. Verification is stdlib-only.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from c020_exact_certificate import pt_integer,walsh,objective,SOURCE,DATA


def verify(cert):
    assert cert['symmetric_support_required'] is True
    assert cert['source_sha256']==hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    u=cert['dual_numerators'];den=cert['dual_denominator']
    assert len(u)==16384 and all(type(v) is int and v>=0 for v in u)
    assert type(den) is int and den>0
    transformed=pt_integer(u)
    freq=walsh(u)
    other=walsh([(-v if ((i%128)&(i//128)).bit_count()%2 else v) for i,v in enumerate(freq)])
    assert other==[128*v for v in transformed]
    c=objective(json.loads(SOURCE.read_text()))
    even=[i for i in range(16384) if not ((i%128)&(i//128)).bit_count()%2]
    assert len(even)==8256
    scores=[c[i]*128*den+transformed[i] for i in even]
    upper=Fraction(max(scores),128*den)
    assert str(upper)==cert['exact_upper']
    # For lambda>=0 on even, sum(lambda)=1, A lambda>=0:
    # c.lambda <= (c+A*u).lambda <= max_even(c+A*u).
    assert Fraction(6)<=upper<Fraction(6)+Fraction(1,10**9)
    return dict(exact_upper=str(upper),decimal_upper=float(upper),gap_above_six=str(upper-6),
                dual_coordinates_checked=16384,symmetric_constraints_checked=len(even),
                exact_bound_six_proved=upper==6,scope='archived C014 Pauli representation')


def build(path):
    import numpy as np
    with np.load(DATA/'c021_bosonic_ppt.npz',allow_pickle=False) as data:
        raw=-data['C014_dual']
    den=10**12
    u=[max(0,int(round(float(v)*den))) for v in raw]
    t=pt_integer(u);c=objective(json.loads(SOURCE.read_text()))
    upper=Fraction(max(c[i]*128*den+t[i] for i in range(16384)
                       if not ((i%128)&(i//128)).bit_count()%2),128*den)
    cert=dict(source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              dual_numerators=u,dual_denominator=den,exact_upper=str(upper),
              symmetric_support_required=True)
    verify(cert)
    with path.open('x',encoding='utf-8') as stream:json.dump(cert,stream,indent=2)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('build','verify'));args=parser.parse_args()
    path=DATA/'c021_exact_dual_certificate.json'
    if args.mode=='build':build(path)
    print(json.dumps(verify(json.loads(path.read_text())),indent=2))
