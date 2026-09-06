"""C003 pinned benchmark screen, exact integer structural enumeration."""
import ast
import hashlib
import json
from pathlib import Path
import urllib.request
from verify_scf_generalization import graph_edges

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'
UPSTREAM = '467eb611c09631fcf310da8dc73c35cb3b8fe098'
BASE = f'https://raw.githubusercontent.com/wangjie212/BetaNumber/{UPSTREAM}/src/seesaw-shadow-tomography/data'
EXPECTED = {8:'96d6ad0be933af0c4f763dc8e5a08d825d413b053235a91cf9340d8ca1a3adbd',
            9:'1eb261786d59004f6373b54016ca55c88a36b6f2bdb01edbe538d71b2f69ede7'}


def fetch(order):
    # Read a matching local immutable source if available; never modify it.
    local = DATA.parents[1]/'.prior_art_BetaNumber'/'src'/'seesaw-shadow-tomography'/'data'/f'test{order}.txt'
    raw = local.read_bytes() if local.exists() else b''
    if hashlib.sha256(raw).hexdigest() != EXPECTED[order]:
        with urllib.request.urlopen(f'{BASE}/test{order}.txt',timeout=30) as response:
            raw = response.read()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED[order]
    entries = [ast.literal_eval(line) for line in raw.decode().splitlines() if line.strip()]
    assert len(entries) == {8:18,9:1419}[order]
    return entries


def separators(code):
    n,edges = graph_edges(code)
    all_nodes = (1 << n)-1
    adjacency = [sum(1 << j for j in range(n) if tuple(sorted((i,j))) in edges) for i in range(n)]
    rows = []
    for boundary in range(1,all_nodes):
        s = [i for i in range(n) if boundary >> i & 1]
        pairs = [(i,j) for i in s for j in s if i < j and (i,j) not in edges]
        if len(pairs) != 1:
            continue
        remaining = all_nodes ^ boundary
        components = []
        while remaining:
            reached = remaining & -remaining
            while True:
                enlarged = reached
                for i in range(n):
                    if reached >> i & 1:
                        enlarged |= adjacency[i] & remaining
                if enlarged == reached:
                    break
                reached = enlarged
            components.append(reached)
            remaining &= ~reached
        if len(components) < 2:
            continue
        for split in range((1 << (len(components)-1))-1):
            left_mask = boundary | components[0]
            for i,component in enumerate(components[1:]):
                if split >> i & 1:
                    left_mask |= component
            right_mask = (all_nodes ^ left_mask) | boundary
            rows.append({'separator':s,'pair':list(pairs[0]),
                         'left':[i for i in range(n) if left_mask >> i & 1],
                         'right':[i for i in range(n) if right_mask >> i & 1]})
    return rows


def main():
    assert len(separators('Cl')) == 2 and separators('C~') == []
    records = []
    sources = {}
    for order in (8,9):
        entries = fetch(order)
        sources[str(order)] = {'url':f'{BASE}/test{order}.txt','sha256':EXPECTED[order],'rows':len(entries)}
        for i,entry in enumerate(entries):
            code = entry[0]
            found = separators(code)
            records.append({'order':order,'source_row':i+1,'graph6':code,'decompositions':found})
        current = [r for r in records if r['order'] == order]
        print(json.dumps({'order':order,'graphs':len(current),'with_separator':sum(bool(r['decompositions']) for r in current),
                          'decompositions':sum(len(r['decompositions']) for r in current)}),flush=True)
    payload = {'experiment':'C003_almost_clique_closure_benchmark_screen',
               'date':'2026-09-06','preregistration_commit':'39d4400','upstream_commit':UPSTREAM,
               'sources':sources,'graphs_screened':len(records),
               'graphs_with_almost_clique_separator':sum(bool(r['decompositions']) for r in records),
               'decompositions_found':sum(len(r['decompositions']) for r in records),
               'generic_quantum_closure_falsified':False,'SCF_conjecture_falsified':False,
               'status':'structural_screen_only_local_and_quantum_certificates_pending','records':records}
    (DATA/'almost_clique_closure_audit.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Assertions required.')
    main()
