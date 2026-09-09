"""Regenerate equality matrix and check deletion identities using Python ints."""
import json
from c020_exact_certificate import DATA,SOURCE,objective
from verify_c025_exact_face import verify as verify_face


def verify(cert):
    face=json.loads((DATA/'c025_exact_face.json').read_text());verify_face(face)
    orbits=json.loads((DATA/'c018_ppt_symmetry.json').read_text())
    z=set(face['forced_zero_coordinates']);active=set(face['forced_active_coordinates'])
    groups=[g for g in orbits['linear_orbits'] if not set(g)&z]
    rows=[g[0] for g in orbits['affine_orbits'] if g[0] in active]
    keep=cert['retained_rows'];drop=cert['deleted_rows'];den=cert['denominator'];nums=cert['numerators']
    assert sorted(keep+drop)==list(range(len(rows)))
    assert type(den) is int and den>0 and len(nums)==len(drop)
    assert all(len(r)==len(keep) and all(type(v) is int for v in r) for r in nums)
    # Independent direct character sums, not the saved NumPy matrix/bincount.
    signs=[1-2*(((v&127)&(v>>7)).bit_count()%2) for v in range(16384)]
    matrix=[[sum(signs[v^u] for u in g) for g in groups] for v in rows]
    c=objective(json.loads(SOURCE.read_text()));rhs=[128*(6-c[v]) for v in rows]
    for d,coeff in zip(drop,nums):
        out=[0]*len(groups);value=0
        for k,n in zip(keep,coeff):
            if not n:continue
            value+=n*rhs[k]
            out=[x+n*y for x,y in zip(out,matrix[k])]
        assert out==[den*v for v in matrix[d]]
        assert value==den*rhs[d]
    assert cert['status']=='exact_redundancy_verified'
    assert cert['remaining_independence_proved'] is False and cert['exact_six_proved'] is False
    return dict(retained_equalities=len(keep),exactly_redundant_equalities=len(drop),
                columns_checked=len(groups),common_denominator=den,
                equivalence_proved=True,remaining_independence_proved=False,exact_six_proved=False)


if __name__=='__main__':
    if not __debug__:raise RuntimeError('Assertions required')
    print(json.dumps(verify(json.loads((DATA/'c027_row_relations_fraction.json').read_text())),indent=2))
