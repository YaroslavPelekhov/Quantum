"""Bounded, stdlib-only novelty diagnostic; not a quantum proof verifier."""
from itertools import combinations
import json


def modules(n, edges):
    # Direct set-based implementation, separate from the initial bitmask run.
    vertices = set(range(n))
    adjacent = lambda u, v: tuple(sorted((u, v))) in edges
    return [list(group) for size in range(2, n)
            for group in combinations(range(n), size)
            if all(len({adjacent(v, u) for u in group}) == 1
                   for v in vertices.difference(group))]


def graph(cells):
    cells = sorted(cells)
    k = len(cells)
    edges = {(i, j) for i, j in combinations(range(k), 2)
             if cells[i][0] == cells[j][0] or cells[i][1] == cells[j][1]}
    edges.update((i, k+h) for i, (r, c) in enumerate(cells) for h in range(3)
                 if (r != h if h < 2 else c != 0))
    edges.update(combinations(range(k, k+3), 2))
    return k+3, edges


def main():
    assert modules(4, {(0, 1), (1, 2), (2, 3)}) == []
    assert modules(4, {(0, 1), (1, 2), (2, 3), (0, 3)}) == [[0, 2], [1, 3]]
    assert modules(3, set(combinations(range(3), 2))) == [[0, 1], [0, 2], [1, 2]]
    cases = [(f'G_{m}', [(r, j) for r in (0, 1) for j in range(m+1)]
              + [(2, 0), (0, m+1), (1, m+2)]) for m in range(5)]
    cases.append(('C008', [(r, c) for r in range(3) for c in range(3)]))
    results = []
    for (name, cells), expected in zip(cases, (1, 3, 6, 10, 15, 12)):
        n, edges = graph(cells)
        found = modules(n, edges)
        holes = [list(s) for s in combinations(range(n), 4)
                 if all(sum(tuple(sorted((u, v))) in edges for u in s if u != v) == 2
                        for v in s)]
        assert found == [] and len(holes) == expected
        results.append(dict(name=name, n=n, proper_nontrivial_modules=found,
                            induced_C4_count=len(holes), first_C4=holes[0]))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
