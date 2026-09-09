"""Exact diagonal specialization, all 255 nonempty three-qubit supports.

Post-hoc structural test, not a random-process ensemble experiment.
The squared filter multiplier is R[c]/M[b,c], avoiding square roots.
"""
from fractions import Fraction as F
import json


def marginals(p):
    m = [p[i] + p[4+i] for i in range(4)]
    return m, [m[c] + m[2+c] for c in range(2)]


def step(p):
    m, r = marginals(p)
    q = [x*r[i % 2]/m[i % 4] if x else F(0) for i, x in enumerate(p)]
    z = sum(q)
    return [x/z for x in q]


def defect(p):
    m, r = marginals(p)
    return sum((m[i]-r[i % 2]/2)**2 for i in range(4))


def run():
    mixed = [F(1, 2)] + [F(0)]*6 + [F(1, 2)]
    assert step(mixed) == mixed and defect(mixed) == F(1, 4)
    checked = 0
    for mask in range(1, 256):
        weights = [F(i+1) if mask >> i & 1 else F(0) for i in range(8)]
        p0 = [x/sum(weights) for x in weights]
        m0, r0 = marginals(p0)
        counts = [sum(m0[2*b+c] > 0 for b in range(2)) for c in range(2)]
        p = p0
        for iteration in range(1, 7):
            p = step(p)
            z = sum(counts[c]**iteration*r0[c] for c in range(2))
            predicted_r = [counts[c]**iteration*r0[c]/z for c in range(2)]
            assert marginals(p)[1] == predicted_r
            predicted = [p0[i]/m0[i % 4]*predicted_r[i % 2]/counts[i % 2]
                         if p0[i] else F(0) for i in range(8)]
            assert p == predicted
            assert sum(x > 0 for x in p) == mask.bit_count()
            assert (defect(p) == 0) == all(n in (0, 2) for n in counts)
            checked += 1
    print(json.dumps(dict(supports=255, exact_iterates=checked,
                          rank_two_mixed_fixed=True, residual_squared='1/4',
                          author_implementation_tested=False), indent=2))


if __name__ == '__main__':
    run()
