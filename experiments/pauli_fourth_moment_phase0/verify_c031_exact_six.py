"""Standalone stdlib exact acceptance of the C014 upper-six certificate."""
import json
from c020_exact_certificate import DATA
from c021_exact_dual import verify
from verify_scf_two_xx_weight import verify as verify_source


def check(cert):
    assert cert['exact_upper']=='6'
    source=json.loads((DATA/'scf_two_xx_weight_c014.json').read_text())
    graph=verify_source(source)
    assert graph['weights'][0]['bound']==6
    result=verify(cert)
    assert result['exact_bound_six_proved'] is True
    result.update(classical_stable_lower_bound=6,
                  fixed_representation_quantum_maximum=6,
                  representation_transfer='Published Xu--Schwonnek--Winter weighted invariance; see C023',
                  unrestricted_SCF_theorem=False,A_star_confirmed=False)
    return result


if __name__=='__main__':
    if not __debug__:raise RuntimeError('Assertions required')
    print(json.dumps(check(json.loads((DATA/'c031_candidate.json').read_text())),indent=2))
