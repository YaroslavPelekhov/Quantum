"""Inspect dependencies of exact C025 equality rows before another LP."""
import json
import time
import numpy as np
from scipy.linalg import qr
from threadpoolctl import threadpool_limits
from c020_exact_certificate import DATA,SOURCE,objective
from verify_c025_exact_face import verify


if __name__=='__main__':
    path=DATA/'c027_equality_rank.json'
    assert not path.exists() and not path.with_suffix('.npz').exists()
    start=time.monotonic();face=json.loads((DATA/'c025_exact_face.json').read_text());verify(face)
    orbits=json.loads((DATA/'c018_ppt_symmetry.json').read_text())
    zero=set(face['forced_zero_coordinates']);active=set(face['forced_active_coordinates'])
    groups=[g for g in orbits['linear_orbits'] if not set(g)&zero]
    rows=[g[0] for g in orbits['affine_orbits'] if g[0] in active]
    assert len(rows)*len(groups)<=10_000_000
    index=np.arange(16384);labels=np.full(16384,len(groups),dtype=int)
    for j,g in enumerate(groups):labels[g]=j
    tau=np.array([(-1)**((i%128)&(i//128)).bit_count() for i in range(16384)])
    mat=np.array([np.bincount(labels,weights=tau[index^v],minlength=len(groups)+1)[:-1] for v in rows])
    assert np.all(mat==np.rint(mat))
    rhs=128*(6-np.array(objective(json.loads(SOURCE.read_text())))[rows])
    with threadpool_limits(limits=1):
        r,piv=qr(mat.T,mode='r',pivoting=True)
    diagonal=np.abs(np.diag(r))
    ranks={str(t):int(sum(diagonal>max(diagonal)*t)) for t in (1e-8,1e-10,1e-12)}
    rank=ranks['1e-10']
    report=dict(rows=len(rows),columns=len(groups),numerical_ranks=ranks,
                max_diagonal=float(max(diagonal)),min_diagonal=float(min(diagonal)),
                last_retained_diagonal=float(diagonal[rank-1]) if rank else None,
                first_discarded_diagonal=float(diagonal[rank]) if rank<len(diagonal) else None,
                seconds=time.monotonic()-start,exact_rank_proved=False,exact_six_proved=False)
    with path.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    with path.with_suffix('.npz').open('xb') as stream:
        np.savez_compressed(stream,matrix=mat.astype(np.int16),rhs=rhs.astype(np.int64),
                            row_representatives=np.array(rows),pivots=piv,diagonal=diagonal)
    print(json.dumps(report,indent=2))
