"""C014 independent exhaustive products, Fraction affine rank and Pauli audit."""
import itertools as it
import json
from verify_scf_two_xx_gate import expected_graph,all_stable_masks,DATA
from verify_scf_generalization import graph_edges
from verify_scf_three_row_gate import simplicial_clique,gf2_rank
from verify_scf_rectangular_gram_bridge import exact_rank


def verify(report):
    assert not any(report[k] for k in ('independent_complete_hull','quantum_target_proved',
                                       'unrestricted_SCF_theorem','A_star_confirmed'))
    core,edges=expected_graph()
    assert graph_edges(report['graph6'])==(24,edges)
    assert simplicial_clique(24,edges,[22,23])
    neighbors=[{j for j in range(24) if tuple(sorted((i,j))) in edges} for i in range(24)]
    assert all(any(tuple(sorted(p)) in edges for p in it.combinations(leaves,2))
               for i in range(24) for leaves in it.combinations(neighbors[i],3))
    masks=all_stable_masks(core,edges)
    assert masks==report['stable_masks']
    assert max(s.bit_count() for s in masks)==report['alpha']
    assert len(report['records'])==2
    # Original one-based 9,10 become zero-based 6,7 after deleting 7,8.
    for row,name,heavy in zip(report['records'],('target_one_weighted_atom','control_two_weighted_atoms'),
                              ({6,7},{6,7,17,18})):
        assert row['name']==name and row['weights']==[1+int(i in heavy) for i in range(24)]
        vals=[sum(row['weights'][i]*(s>>i&1) for i in range(24)) for s in masks]
        assert max(vals)==row['stable_bound']
        tight=[s for s,v in zip(masks,vals) if v==max(vals)]
        assert tight==row['tight_masks']
        rank=exact_rank([[1]+[s>>i&1 for i in range(24)] for s in tight],25)
        assert rank==row['homogeneous_rank'] and row['facet_inducing']==(rank==24)
    assert report['records'][1]['stable_bound']==7
    labels=report['standard_SAUR_labels']; qubits=report['minimal_qubits']
    assert len(labels)==24 and all(0<=x<1<<qubits and 0<=z<1<<qubits for x,z in labels)
    assert all(bool(((x&v).bit_count()+(z&u).bit_count())%2)==((i,j) in edges)
               for i,(x,z) in enumerate(labels) for j,(u,v) in enumerate(labels) if i<j)
    rank=gf2_rank(24,edges)
    assert rank==2*qubits
    return dict(status='C014_exact_frozen_weight_faces_and_SAUR_verified',
                STAB_vertices=len(masks),alpha=report['alpha'],binary_rank=rank,minimal_qubits=qubits,
                weights=[dict(name=r['name'],bound=r['stable_bound'],tight_sets=len(r['tight_masks']),
                              rank=r['homogeneous_rank'],facet=r['facet_inducing']) for r in report['records']],
                quantum_target_proved=False,unrestricted_SCF_theorem=False,A_star_confirmed=False)


if __name__=='__main__':
    if not __debug__:raise RuntimeError('Assertions required')
    print(json.dumps(verify(json.loads((DATA/'scf_two_xx_weight_c014.json').read_text()))))
