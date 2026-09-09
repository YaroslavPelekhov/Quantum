"""Registered C025-face LP and full-coordinate rational recovery."""
import json
import numpy as np
from threadpoolctl import threadpool_limits
from run_c022_exact_six import run, DATA
from recover_c022_exact import run as recover


if __name__ == '__main__':
    path=DATA/'c026_exact_six.json'
    assert not path.exists() and not path.with_suffix('.npz').exists()
    face=json.loads((DATA/'c025_exact_face.json').read_text())
    with threadpool_limits(limits=1):
        report,arrays=run(method='highs-ipm',minimize_orbit_sum=True,exact_face=face)
    with path.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    with path.with_suffix('.npz').open('xb') as stream:np.savez_compressed(stream,**arrays)
    print(json.dumps(report,indent=2),flush=True)
    recovered=recover('c026')
    with (DATA/'c026_recovery.json').open('x',encoding='utf-8') as stream:
        json.dump(recovered,stream,indent=2)
    print(json.dumps(recovered,indent=2),flush=True)
