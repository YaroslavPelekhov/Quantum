"""Exact witness of the G8 induced subgraph inside the campaign G9.

No optimizer, graph-isomorphism library or engine import. Does not infer
equivalence of physical noisy tasks or equality of the weighted beta numbers.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def anti(a, b):
    return sum(x != y and x != 'I' and y != 'I' for x, y in zip(a, b)) % 2


def symplectic(a, b):
    encode = lambda s: (sum((c in 'XY') << j for j, c in enumerate(s)),
                        sum((c in 'YZ') << j for j, c in enumerate(s)))
    x, z = encode(a); xx, zz = encode(b)
    return ((x & zz).bit_count() + (z & xx).bit_count()) % 2


def verify_map(words8, weights8, words9, weights9, mapping):
    assert len(mapping) == 8 and len(set(mapping)) == 8
    for i in range(8):
        assert weights8[i] == weights9[mapping[i]]
        for j in range(8):
            old = anti(words8[i], words8[j])
            new = symplectic(words9[mapping[i]], words9[mapping[j]])
            assert old == new, (i, j)


def main():
    record = json.loads((ROOT/'results/pauli_fourth_moment_phase0/almost_clique_closure_counterexample.json').read_text())
    words8, w8 = record['pauli_words'], record['weights']
    words9 = ['XIII', 'IXII', 'IIXI', 'ZIII', 'IZII', 'ZZZI', 'YZYX', 'YYXX', 'YXZZ']
    w9 = [1]*7+[2, 2]
    mapping = list(range(1, 9))
    verify_map(words8, w8, words9, w9, mapping)
    # Corrupt a weight and an observable; acceptance must reject both.
    broken = w9.copy(); broken[1] += 1
    for words, weights in [(words9, broken), (words9[:1]+['IIII']+words9[2:], w9)]:
        try:
            verify_map(words8, w8, words, weights, mapping)
        except AssertionError:
            pass
        else:
            raise AssertionError('Corruption accepted')
    print(json.dumps(dict(status='verified', G8_to_G9_zero_based=mapping,
                          omitted_G9_vertex=0, omitted_word=words9[0], omitted_weight=1,
                          weights_preserved=True, corrupted_controls_rejected=2,
                          noisy_task_equivalence_claimed=False), indent=2))


if __name__ == '__main__':
    main()
