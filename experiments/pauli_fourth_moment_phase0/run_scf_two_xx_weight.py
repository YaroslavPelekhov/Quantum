"""C014 exact two frozen weights; no complete hull or quantum optimization."""
import json
import time
import networkx as nx
import sympy as sp
from run_scf_two_xx_gate import target_graph,stable_sets,DATA
from run_scf_hbar_falsification import standard_saur


def main():
    start=time.monotonic()
    g=target_graph(); masks=stable_sets(g)
    labels=[i for i in range(1,14) if i not in (7,8)]
    left=[labels.index(i) for i in (9,10)]
    records=[]
    for name,heavy in [('target_one_weighted_atom',left),
                       ('control_two_weighted_atoms',left+[i+11 for i in left])]:
        w=[1+int(i in heavy) for i in range(24)]
        vals=[sum(w[i]*(s>>i&1) for i in range(24)) for s in masks]
        bound=max(vals); roots=[s for s,v in zip(masks,vals) if v==bound]
        rank=int(sp.Matrix([[1]+[s>>i&1 for i in range(24)] for s in roots]).rank())
        records.append(dict(name=name,weights=w,stable_bound=bound,tight_masks=roots,
                            homogeneous_rank=rank,facet_inducing=rank==24))
    paulis,qubits=standard_saur(g)
    result=dict(experiment='C014_two_XX_exact_weights',preregistration_commit='6456fed',
                graph6=nx.to_graph6_bytes(g,header=False).decode().strip(),stable_masks=masks,
                alpha=max(s.bit_count() for s in masks),records=records,
                standard_SAUR_labels=paulis,minimal_qubits=qubits,
                independent_complete_hull=False,quantum_target_proved=False,
                unrestricted_SCF_theorem=False,A_star_confirmed=False)
    assert time.monotonic()-start<300
    (DATA/'scf_two_xx_weight_c014.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(graph6=result['graph6'],STAB_vertices=len(masks),alpha=result['alpha'],
                          qubits=qubits,records=[{k:v for k,v in r.items() if k!='tight_masks'} for r in records])))


if __name__=='__main__':main()
