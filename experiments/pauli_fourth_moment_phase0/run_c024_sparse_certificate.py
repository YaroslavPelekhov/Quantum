"""One preregistered minimum-orbit-mass interior-point certificate attempt."""
import json
import numpy as np
from threadpoolctl import threadpool_limits
from run_c022_exact_six import run, DATA
from recover_c022_exact import run as recover


if __name__ == '__main__':
    path = DATA / 'c024_exact_six.json'
    assert not path.exists() and not path.with_suffix('.npz').exists()
    with threadpool_limits(limits=1):
        report, arrays = run(method='highs-ipm', minimize_orbit_sum=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    with path.with_suffix('.npz').open('xb') as stream:
        np.savez_compressed(stream, **arrays)
    print(json.dumps(report, indent=2), flush=True)
    recovery = recover('c024')
    with (DATA / 'c024_recovery.json').open('x', encoding='utf-8') as stream:
        json.dump(recovery, stream, indent=2)
    print(json.dumps(recovery, indent=2), flush=True)
