# External baseline reproducibility audit

Audit date: 2026-08-03.

## GAT parameter-transfer baseline

- Paper: Xu et al., *Graph Attention Networks for Transferable QAOA Parameter Initialization*, HPEC 2025 / arXiv:2504.21135.
- Public repository: `jxsoortha/QAOA-Parameter-Transfer-via-GAT`, commit `ab8434ffcb2cfcac16d136d8677f327752d9ca8d` (2025-09-04), Apache-2.0.
- Local immutable audit copy: `baselines/QAOA-Parameter-Transfer-via-GAT`.
- The repository includes a no-edge-feature eight-cluster MIS checkpoint and parameter/cluster tables.
- The checked-in large-graph evaluation script is not directly executable at that commit. It requires `mis_output_2p`, which is absent, and requests 24-node train/test graph2vec files that are also absent at the expected paths. The only non-temporary large-graph training embedding is for 28 nodes; several alternative files exist under a `temp` directory but do not satisfy the script's declared paths.
- The evaluation is also not apples-to-apples with this artifact: it uses ER donor/acceptor graphs, depth two with a fixed 1.5 QUBO penalty, learned Node2Vec/GAT cluster selection, and target-specific embeddings. Our primary claim concerns a single graph-independent schedule, trained on QOBLIB-derived graphs and applied without target adaptation.
- The public script passes only the keys of a `qml.counts()` dictionary to its occurrence counter, so the reported loop does not use shot multiplicities. We do not silently patch this behavior because doing so would define a new baseline not identical to the released evaluation.

Decision: cite and discuss the method as the closest learned transfer comparator, report its substantially higher supervision/adaptation requirements, and explicitly mark direct QOBLIB numerical reproduction as unavailable from the released artifact. Do not insert invented GAT numbers into the comparison table.

## Graph-conditioned meta-optimizer

Nguyen and Safro, arXiv:2604.25275, is a contemporaneous graph-conditioned parameter-generator direction. No public implementation or pretrained checkpoint was identified in the paper metadata or targeted web/repository search as of the audit date. It is therefore a related-work comparator, not a runnable baseline.
