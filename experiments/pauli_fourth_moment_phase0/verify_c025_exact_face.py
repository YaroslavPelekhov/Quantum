"""Independent completeness count and exact primal-face checks, stdlib only."""
import hashlib
import json
import math
from c020_exact_certificate import DATA,SOURCE,objective,pt_integer,walsh
from verify_scf_two_xx_weight import verify as verify_source


def span(generators):
    out={0}
    for v in generators:out|={x^v for x in out}
    return out


def symplectic(a,b):
    return (((a&127)&(b>>7))^((b&127)&(a>>7))).bit_count()%2


def verify(cert):
    source=json.loads(SOURCE.read_text());verify_source(source)
    assert cert['source_sha256']==hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    labels=[x|(z<<7) for x,z in source['standard_SAUR_labels']]
    starts=[span([v for i,v in enumerate(labels) if mask>>i&1])
            for mask in source['records'][0]['tight_masks']]
    spaces=[];lam=[0]*16384;mu=[0]*16384;c=objective(source)
    for record in cert['spaces']:
        b=record['basis'];shift=record['shift'];space=span(b)
        assert len(b)==7 and len(space)==128 and all(0<=v<16384 for v in space)
        assert all(symplectic(a,d)==0 for a in b for d in b)
        assert 0<=shift<16384 and all(symplectic(shift,p)==((p&127)&(p>>7)).bit_count()%2 for p in b)
        assert any(s<=space for s in starts)
        coset={shift^p for p in space}
        assert all(((v&127)&(v>>7)).bit_count()%2==0 for v in coset)
        assert sum(c[v] for v in coset)==768
        spaces.append(frozenset(space))
        for v in space:mu[v]+=1
        for v in coset:lam[v]+=1
    assert len(set(spaces))==len(spaces)==cert['maximal_isotropic_spaces']
    # Number of Lagrangian extensions of isotropic rank r in 2n dimensions:
    # quotient S^perp/S is symplectic of dimension 2(n-r).
    # Count Lagrangians by incidences: N_k(2^k-1)=(2^(2k)-1)N_(k-1).
    # Hence N_k=product_(j=1..k)(2^j+1), N_0=1.
    hist={}
    for s in starts:
        r=len(s).bit_length()-1;hist[str(r)]=hist.get(str(r),0)+1
        expected=math.prod(2**j+1 for j in range(1,8-r))
        assert sum(s<=space for space in spaces)==expected
    assert hist==cert['stable_span_rank_histogram']
    assert cert['complete_enumeration'] is True
    assert lam==cert['aggregate_lambda_numerators'] and mu==cert['aggregate_pt_numerators']
    assert sum(lam)==sum(mu)==cert['aggregate_denominator']==128*len(spaces)
    assert pt_integer(lam)==[128*v for v in mu]
    freq=walsh(lam)
    second=walsh([(-v if ((i&127)&(i>>7)).bit_count()%2 else v) for i,v in enumerate(freq)])
    assert second==[16384*v for v in mu]
    assert sum(c[i]*lam[i] for i in range(16384))==6*sum(lam)
    zeros=[i for i,v in enumerate(mu) if v];active=[i for i,v in enumerate(lam) if v]
    assert zeros==cert['forced_zero_coordinates'] and active==cert['forced_active_coordinates']
    orbits=json.loads((DATA/'c018_ppt_symmetry.json').read_text())
    z=set(zeros);a=set(active)
    assert all(not set(g)&z or set(g)<=z for g in orbits['linear_orbits'])
    assert all(not set(g)&a or set(g)<=a for g in orbits['affine_orbits'])
    assert sum(not bool(set(g)&z) for g in orbits['linear_orbits'])==cert['remaining_linear_orbits']
    assert sum(bool(set(g)&a) for g in orbits['affine_orbits'])==cert['forced_active_affine_orbits']
    assert cert['exact_objective']=='6' and cert['exact_six_upper_proved'] is False
    return dict(complete_spaces=len(spaces),independently_counted_extensions_per_stable_set=15,
                forced_zeros=len(zeros),forced_equalities=len(active),
                exact_primal_objective=6,exact_six_upper_proved=False)


if __name__=='__main__':
    if not __debug__:raise RuntimeError('Assertions required')
    print(json.dumps(verify(json.loads((DATA/'c025_exact_face.json').read_text())),indent=2))
