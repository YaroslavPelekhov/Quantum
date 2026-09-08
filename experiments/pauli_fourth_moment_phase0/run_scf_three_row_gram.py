"""C009 exact discovery. Inversion parity, full universal polynomials."""
import itertools as it
import json
import time
from pathlib import Path
from verify_scf_rectangular_gram_bridge import Algebra

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


class ParityAlgebra(Algebra):
    def mul(self, p, q):
        out = {}
        for (u, a), c in p.items():
            for (v, b), d in q.items():
                sign = (-1)**sum((j, i) in self.edges for i in u for j in v if i > j)
                word = tuple(sorted(set(u) ^ set(v)))
                key = word, tuple(x+y for x, y in zip(a, b))
                out[key] = out.get(key, 0)+sign*c*d
        return {k: v for k, v in out.items() if v}


def encode(poly):
    return [{'word': list(w), 'powers': list(p), 'coefficient': c}
            for (w, p), c in sorted(poly.items())]


def calculate(algebra=ParityAlgebra):
    start = time.monotonic()
    n = 12
    edges = set(it.combinations((9, 10, 11), 2))
    edges.update((i, j) for i, j in it.combinations(range(9), 2)
                 if i//3 == j//3 or i%3 == j%3)
    edges.update((i, 9+h) for i in range(9) for h in range(3)
                 if (i//3 != h if h < 2 else i%3 != 0))
    alg = algebra(n, edges)
    one = alg.constant(1)
    a = [alg.variable(i) for i in range(n)]
    p = [{((i,), (0,)*n): 1} for i in range(n)]

    def word(vertices, sign=-1):
        value = alg.constant(sign)
        for i in vertices:
            value = alg.mul(value, p[i])
        return value

    K = [word((9, 10, j, 3+j)) for j in range(3)]
    lam = [one]+[word((0, 6, j, 6+j)) for j in (1, 2)]
    centers = K+lam[1:]
    center_checks = []
    for center in centers:
        ((w, powers), c), = center.items()
        hermitian = word(tuple(reversed(w)), c) == center
        center_checks.append(dict(expression=encode(center), hermitian=hermitian,
                                  involution=alg.sq(center) == one,
                                  noncommuting_generators=[i for i in range(n)
                                      if alg.mul(center, p[i]) != alg.mul(p[i], center)]))
    mutually_commuting = all(alg.mul(x, y) == alg.mul(y, x)
                             for x, y in it.combinations(centers, 2))
    B = [[a[j] for j in range(3)], [alg.mul(K[j], a[3+j]) for j in range(3)],
         [alg.mul(lam[j], a[6+j]) for j in range(3)]]
    M = [[alg.add(*(alg.mul(B[i][k], B[j][k]) for k in range(3)))
          for j in range(3)] for i in range(3)]
    second = alg.add(*(alg.det([[M[i][j] for j in s] for i in s])
                       for s in it.combinations(range(3), 2)))
    heavy = alg.add(*(alg.mul(alg.mul(a[9+i], M[i][j]), a[9+j])
                      for i in range(2) for j in range(2)),
                    alg.mul(alg.sq(a[11]), alg.add(*(alg.sq(B[i][0]) for i in range(3)))))
    rhs = [alg.add(*(M[i][i] for i in range(3)), *(alg.sq(a[i]) for i in (9, 10, 11))),
           alg.add(second, heavy), alg.det(M)]
    independent = [[s for s in it.combinations(range(n), k)
                    if not any(pair in edges for pair in it.combinations(s, 2))] for k in range(5)]
    assert independent[3] and not independent[4]
    charges = [{(s, tuple(int(i in s) for i in range(n))): 1 for s in group}
               for group in independent[:4]]
    full = [alg.add(*(alg.scale(alg.mul(charges[i], charges[d-i]), (-1)**i)
                      for i in range(4) if 0 <= d-i < 4)) for d in range(7)]
    coeff = [alg.scale(full[2*k], (-1)**k) for k in range(1, 4)]
    diff = [alg.add(x, alg.scale(y, -1)) for x, y in zip(coeff, rhs)]
    assert time.monotonic()-start < 300
    return dict(experiment='C009_fixed_three_row_Gram', date='2026-09-08',
                preregistration_commit='9b657c5', graph6='K{S{aSfF~Fln',
                central_checks=center_checks, mutually_commuting=mutually_commuting,
                stable_set_counts=list(map(len, independent)),
                constant_ok=full[0] == one, odd_zero=[not full[d] for d in (1, 3, 5)],
                transfer_coefficients=list(map(encode, coeff)),
                candidate_coefficients=list(map(encode, rhs)),
                residuals=list(map(encode, diff)),
                identity_pass=[not d for d in diff],
                quantum_bound_proved=False, unrestricted_SCF_theorem=False, A_star_confirmed=False)


def main():
    if not __debug__:
        raise RuntimeError('Assertions required')
    result = calculate()
    (DATA/'scf_three_row_gram_c009.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('central_checks', 'mutually_commuting',
                     'stable_set_counts', 'odd_zero', 'identity_pass')}))
    print('residual term counts:', list(map(len, result['residuals'])))


if __name__ == '__main__':
    main()
