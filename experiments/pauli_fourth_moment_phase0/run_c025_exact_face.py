"""Exact face constraints from saturated stabilizer spaces; no optimizer."""
import collections
import hashlib
import json
import time
from c020_exact_certificate import DATA, SOURCE, objective, pt_integer, walsh
from verify_scf_two_xx_weight import verify as verify_source


def sp(a,b):
    return (((a%128)&(b//128)).bit_count()+((a//128)&(b%128)).bit_count())%2


def q(a):
    return ((a%128)&(a//128)).bit_count()%2


def basis(space):
    pivots={}
    for a in sorted(space):
        while a:
            k=a.bit_length()-1
            if k not in pivots:
                pivots[k]=a;break
            a^=pivots[k]
    return list(pivots.values())


def run():
    start=time.monotonic()
    source=json.loads(SOURCE.read_text());verify_source(source)
    labels=[x+128*z for x,z in source['standard_SAUR_labels']]
    seen=set();complete=set();ranks=collections.Counter()
    def extend(space):
        assert time.monotonic()-start<120, 'enumeration time cap'
        key=tuple(sorted(space))
        if key in seen:return
        seen.add(key)
        if len(space)==128:
            complete.add(key)
            assert len(complete)<=10000, 'space count cap'
            return
        b=basis(space)
        perp={v for v in range(16384) if all(not sp(v,p) for p in b)}
        remaining=perp-space
        while remaining:
            v=min(remaining);coset={v^p for p in space}
            remaining-=coset
            extend(space|coset)
    for mask in source['records'][0]['tight_masks']:
        space={0}
        for i,p in enumerate(labels):
            if mask>>i&1:space|={v^p for v in space}
        ranks[len(space).bit_length()-1]+=1
        extend(space)
    c=objective(source);lam=[0]*16384;mu=[0]*16384;records=[]
    for space in sorted(complete):
        assert time.monotonic()-start<120, 'verification time cap'
        b=basis(space)
        assert len(b)==7 and all(not sp(a,d) for a in b for d in b)
        shift=next(v for v in range(16384) if all(sp(v,p)==q(p) for p in b))
        coset=sorted(shift^p for p in space)
        assert all(q(v)==0 for v in coset)
        assert sum(c[v] for v in coset)==6*128
        for v in space:mu[v]+=1
        for v in coset:lam[v]+=1
        records.append(dict(basis=b,shift=shift))
    # Aggregated primal has lambda=lam/(128*number of spaces).
    transformed=pt_integer(lam)
    assert transformed==[128*v for v in mu]
    freq=walsh(lam)
    other=walsh([(-v if q(i) else v) for i,v in enumerate(freq)])
    assert other==[16384*v for v in mu]
    assert sum(lam)==sum(mu)==128*len(complete)
    zeros=[i for i,v in enumerate(mu) if v];active=[i for i,v in enumerate(lam) if v]
    orbits=json.loads((DATA/'c018_ppt_symmetry.json').read_text())
    zero_set=set(zeros);active_set=set(active)
    assert all(not (set(g)&zero_set) or set(g)<=zero_set for g in orbits['linear_orbits'])
    assert all(not (set(g)&active_set) or set(g)<=active_set for g in orbits['affine_orbits'])
    return dict(source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                complete_enumeration=True,stable_span_rank_histogram=dict(ranks),
                maximal_isotropic_spaces=len(complete),spaces=records,
                aggregate_lambda_numerators=lam,aggregate_pt_numerators=mu,
                aggregate_denominator=128*len(complete),exact_objective='6',
                forced_zero_coordinates=zeros,forced_active_coordinates=active,
                remaining_linear_orbits=sum(not bool(set(g)&zero_set) for g in orbits['linear_orbits']),
                forced_active_affine_orbits=sum(bool(set(g)&active_set) for g in orbits['affine_orbits']),
                seconds=time.monotonic()-start,exact_six_upper_proved=False)


if __name__=='__main__':
    result=run()
    with (DATA/'c025_exact_face.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in
          ('spaces','aggregate_lambda_numerators','aggregate_pt_numerators',
           'forced_zero_coordinates','forced_active_coordinates')},indent=2))
    print('Forced zero / active coordinates:',len(result['forced_zero_coordinates']),len(result['forced_active_coordinates']))
