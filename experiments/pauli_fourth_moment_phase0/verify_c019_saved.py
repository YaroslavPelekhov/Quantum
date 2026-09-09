"""Read-only full-coordinate audit using Walsh convolution, not staged PT."""
import json
from pathlib import Path
import numpy as np


def hadamard(v):
    a=v.copy();n=len(a);width=1
    while width<n:
        blocks=a.reshape(-1,2*width)
        left=blocks[:,:width].copy();right=blocks[:,width:].copy()
        blocks[:,:width]=left+right;blocks[:,width:]=left-right;width*=2
    return a


if __name__=='__main__':
    base=Path('results/pauli_fourth_moment_phase0')
    report=json.loads((base/'c019_ppt_cuts.json').read_text())
    source=json.loads((base/'scf_two_xx_weight_c014.json').read_text())
    n=16384;d=128
    sign=np.array([(-1)**((v%128)&(v//128)).bit_count() for v in range(n)])
    obj=np.array([sum(w*(-1)**((x&z).bit_count()+((v%128)&z).bit_count()+((v//128)&x).bit_count())
                     for (x,z),w in zip(source['standard_SAUR_labels'],source['records'][0]['weights']))
                  for v in range(n)])
    with np.load(base/'c019_ppt_cuts.npz',allow_pickle=False) as data:
        assert np.array_equal(obj,data['objective'])
        for row in report['history']:
            p=data[f"lambda_{row['iteration']}"]
            assert abs(sum(p)-1)<1e-8 and min(p)>=-1e-9
            mu=hadamard(sign*hadamard(p))/n
            assert abs(min(mu)-row['min_pt'])<1e-12
            assert abs(obj@p-row['value'])<1e-10
            assert min(mu)<-1e-9
    print(json.dumps(dict(saved_candidates=len(report['history']),all_fail_full_PPT=True,
                          endpoint_recomputed=True,physical_counterexample=False)))
