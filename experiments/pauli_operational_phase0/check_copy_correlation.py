"""Exact rational control fixture, not a claim of a new non-IID theorem."""
from fractions import Fraction as F
import json


def matrix(rows):
    return [[F(x) for x in row] for row in rows]


def trace_product(a, b):
    return sum(a[i][j]*b[j][i] for i in range(len(a)) for j in range(len(a)))


def marginal(a, side):
    if side == 0:
        return [[sum(a[2*i+k][2*j+k] for k in range(2)) for j in range(2)] for i in range(2)]
    return [[sum(a[2*k+i][2*k+j] for k in range(2)) for j in range(2)] for i in range(2)]


def main():
    Q = matrix([[1,0,0,1],[0,-1,1,0],[0,1,-1,0],[1,0,0,1]])
    X = matrix([[0,1],[1,0]]); Z = matrix([[1,0],[0,-1]])
    independent = [[F(i == j, 4) for j in range(4)] for i in range(4)]
    classical = [[F(i == j and i in (0,3), 2) for j in range(4)] for i in range(4)]
    bell = [[F(i in (0,3) and j in (0,3), 2) for j in range(4)] for i in range(4)]
    rows = []
    for name, rho, expected in [('independent', independent, 0), ('classical', classical, 1), ('bell', bell, 2)]:
        assert sum(rho[i][i] for i in range(4)) == 1
        assert all(rho[i][j] == rho[j][i] for i in range(4) for j in range(4))
        # Exact positivity: the first two matrices are nonnegative diagonal;
        # the third is a symmetric idempotent, hence an orthogonal projector.
        if name != 'bell':
            assert all(rho[i][i] >= 0 for i in range(4))
            assert all(rho[i][j] == 0 for i in range(4) for j in range(4) if i != j)
        else:
            assert [[sum(rho[i][k]*rho[k][j] for k in range(4)) for j in range(4)] for i in range(4)] == rho
        for side in (0,1):
            reduced = marginal(rho, side)
            assert reduced == matrix([[F(1,2),0],[0,F(1,2)]])
            assert trace_product(reduced,X)**2 + trace_product(reduced,Z)**2 == 0
        value = trace_product(Q,rho)
        assert value == expected
        rows.append(dict(state=name, pair_expectation=str(value), marginal_functional='0'))
    assert rows[1]['pair_expectation'] != rows[1]['marginal_functional']
    print(json.dumps(dict(status='exact_controls_passed', rows=rows,
                         proves_arbitrary_N=False, novelty_claim=False), indent=2))


if __name__ == '__main__':
    main()
