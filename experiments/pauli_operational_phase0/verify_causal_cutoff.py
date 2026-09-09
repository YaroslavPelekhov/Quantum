"""Read-only saved-state audit, no sampler imports; SVD norm endpoints."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits


def suffix(a,n):
    return sum(a[h*n:(h+1)*n,h*n:(h+1)*n] for h in range(len(a)//n))


def verify(path):
    report=json.loads(path.read_text(encoding='utf-8'))
    archive=path.with_suffix('.npz')
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==report['state_archive_sha256']
    with np.load(archive,allow_pickle=False) as states:
        assert len(states.files)==len(report['rows'])==75
        fresh={}
        for row in report['rows']:
            key=row['state_key']
            rho=states[key]
            assert rho.shape==(32,32) and np.all(np.isfinite(rho))
            assert np.max(abs(rho-rho.conj().T))<1e-9
            assert abs(np.trace(rho)-1)<1e-9 and min(np.linalg.eigvalsh(rho))>-1e-9
            pt=np.empty_like(rho)
            for i in range(32):
                for j in range(32):
                    pt[i,j]=rho[(j//8)*8+i%8,(i//8)*8+j%8]
            neg=float((sum(np.linalg.svd(pt,compute_uv=False))-1)/2)
            residual=max(np.linalg.norm(suffix(rho,n)-np.kron(np.eye(2)/2,suffix(rho,n//2)))
                         for n in (4,16))
            assert abs(neg-row['negativity'])<1e-12
            assert abs(residual-row['residual'])<1e-12
            assert (residual<=1e-9)==row['accepted']
            assert abs(np.vdot(rho,rho).real-row['purity'])<1e-12
            fresh[key]=neg
        primary=[]
        for pair in report['pairs']:
            a=f"r{pair['rank_input']}_seed{pair['seed']}_cut{pair['left']:.0e}"
            b=f"r{pair['rank_input']}_seed{pair['seed']}_cut{pair['right']:.0e}"
            delta=abs(fresh[a]-fresh[b])
            dist=float(sum(np.linalg.svd(states[a]-states[b],compute_uv=False))/2)
            assert abs(delta-pair['negativity_delta'])<1e-12
            assert abs(dist-pair['trace_distance'])<1e-12
            if pair['rank_input']==2 and pair['left']==1e-8 and pair['right']==1e-14:
                primary.append(delta)
        assert len(primary)==20 and float(np.median(primary))<.01
        assert report['primary_gate']=='fail'
    return dict(states_verified=75,pairs_verified=len(report['pairs']),
                primary_gate='fail',sampler_imported=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    with threadpool_limits(limits=1):
        print(json.dumps(verify(args.report),indent=2))
